import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="VLOOKUP السريع لملفات الإكسيل", page_icon="📊", layout="wide")

# 🎨 تطبيق الخلفية السوداء والنصوص البيضاء
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    .stButton>button {
        background-color: #262730;
        color: #FFFFFF;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ أداة مطابقة جلب البيانات السريعة (تعدد الشيتات وجلب أحدث تاريخ)")
st.write("ربط وجلب البيانات من عدة شيتات مع اختيار أحدث تاريخ تلقائياً في حالة تكرار رقم الطلب.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 1. الشيت الأساسي (الملف الصغير)")
    target_file = st.file_uploader("ارفع الملف المراد إضافة البيانات إليه (Excel/CSV):", type=["xlsx", "xls", "csv"], key="target")

with col2:
    st.subheader("📁 2. شيت المصدر (الملف الكبير المتعدد الشيتات)")
    source_file = st.file_uploader("ارفع الملف الذي يحتوي على البيانات الكلية (Excel/CSV):", type=["xlsx", "xls", "csv"], key="source")

if target_file and source_file:
    try:
        with st.spinner("جاري قراءة الملفات وفحص الشيتات..."):
            # قراءة الملف الأساسي
            df_target = pd.read_csv(target_file) if target_file.name.endswith('.csv') else pd.read_excel(target_file)
            
            # قراءة ملف المصدر والتعرف على أسماء الشيتات
            if source_file.name.endswith('.csv'):
                excel_sheets = {"Sheet1": pd.read_csv(source_file)}
                sheet_names = ["Sheet1"]
            else:
                xls_source = pd.ExcelFile(source_file)
                sheet_names = xls_source.sheet_names

        st.success("✅ تم تحميل الملفين بنجاح!")
        st.divider()

        st.subheader("⚙️ إعدادات الشيتات والأولوية والربط")

        # اختيار وترتيب الشيتات
        selected_sheets_order = st.multiselect(
            "📑 حدد الشيتات المراد البحث فيها ورتّبها حسب الأولوية (مثال: زيادة الحد ثم موسى ثم كارت اسلامي...):",
            options=sheet_names,
            default=sheet_names
        )

        if not selected_sheets_order:
            st.warning("⚠️ يرجى اختيار شيت واحد على الأقل من ملف المصدر للبدء.")
        else:
            with st.spinner("جاري تجميع الشيتات المختارة بالترتيب المحدد..."):
                if source_file.name.endswith('.csv'):
                    df_source_combined = excel_sheets["Sheet1"]
                else:
                    frames = [pd.read_excel(xls_source, sheet_name=sheet) for sheet in selected_sheets_order]
                    df_source_combined = pd.concat(frames, ignore_index=True)

            cfg_col1, cfg_col2 = st.columns(2)

            with cfg_col1:
                target_key = st.selectbox("اختر عمود البحث (الـ Key/رقم الطلب) في الشيت الأساسي:", df_target.columns)
            
            with cfg_col2:
                source_key = st.selectbox("اختر عمود البحث (الـ Key/رقم الطلب) في شيت المصدر:", df_source_combined.columns)

            # خيار اختيار عمود التاريخ للمفاضلة عند التكرار
            st.markdown("---")
            st.subheader("📅 تصفية التكرار حسب أحدث تاريخ")
            
            use_date_sort = st.checkbox("تفعيل التصفية حسب أحدث تاريخ (في حالة تكرار رقم الطلب)", value=True)
            
            date_col = None
            if use_date_sort:
                date_col = st.selectbox(
                    "اختر عمود التاريخ في شيت المصدر (لاختيار أحدث تاريخ دائماً):",
                    options=df_source_combined.columns
                )

            # اختيار الأعمدة المراد نقلها
            available_columns = [col for col in df_source_combined.columns if col != source_key]
            selected_columns = st.multiselect(
                "📌 اختر الأعمدة المراد جلبها إلى الشيت الأساسي:",
                options=available_columns,
                default=available_columns[:1] if available_columns else []
            )

            if selected_columns:
                if st.button("🚀 تنفيذ عملية الدمج وجلب البيانات الفورية"):
                    with st.spinner("جاري معالجة البيانات واختيار أحدث تاريخ..."):
                        cols_to_fetch = [source_key] + selected_columns
                        if use_date_sort and date_col and date_col not in cols_to_fetch:
                            cols_to_fetch.append(date_col)

                        df_source_filtered = df_source_combined[cols_to_fetch].copy()

                        # فرز وتصفية أحدث تاريخ
                        if use_date_sort and date_col:
                            # تحويل العمود لتاريخ لضمان الترتيب الصحيح
                            df_source_filtered[date_col] = pd.to_datetime(df_source_filtered[date_col], errors='coerce')
                            # ترتيب تنازلي حسب التاريخ (الأحدث في الأعلى)
                            df_source_filtered = df_source_filtered.sort_values(by=date_col, ascending=False)

                        # إزالة التكرارات مع الاحتفاظ بالظهور الأول (الذي يمثل أحدث تاريخ)
                        df_source_filtered = df_source_filtered.drop_duplicates(subset=[source_key], keep='first')

                        # عملية الدمج المباشر
                        merged_df = pd.merge(
                            df_target,
                            df_source_filtered,
                            left_on=target_key,
                            right_on=source_key,
                            how='left'
                        )

                        if target_key != source_key and source_key in merged_df.columns:
                            merged_df.drop(columns=[source_key], inplace=True)

                    st.success(f"🎉 تم جلب أحدث البيانات بنجاح لـ {len(merged_df)} صف!")
                    
                    st.subheader("📋 معاينة النتيجة:")
                    st.dataframe(merged_df.head(20), use_container_width=True)

                    # تجهيز ملف Excel للتحميل
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        merged_df.to_excel(writer, index=False, sheet_name='البيانات المدمجة')
                    excel_bytes = output.getvalue()

                    st.download_button(
                        label="📥 تحميل الشيت المدمج (Excel)",
                        data=excel_bytes,
                        file_name="vlookup_latest_date_result.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة أو دمج الملفات: {e}")
