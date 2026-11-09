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

st.title("⚡ أداة مطابقة جلب البيانات (أولوية الشيتات الصارمة)")
st.write("جلب البيانات بالترتيب: الشيت الأول ⬅️ ثم استكمال المتبقي من الشيت الثاني ⬅️ ثم الثالث...")

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
            df_target = pd.read_csv(target_file) if target_file.name.endswith('.csv') else pd.read_excel(target_file)
            
            if source_file.name.endswith('.csv'):
                excel_sheets = {"Sheet1": pd.read_csv(source_file)}
                sheet_names = ["Sheet1"]
            else:
                xls_source = pd.ExcelFile(source_file)
                sheet_names = xls_source.sheet_names

        st.success("✅ تم تحميل الملفين بنجاح!")
        st.divider()

        st.subheader("⚙️ إعدادات الشيتات والأولوية والربط")

        selected_sheets_order = st.multiselect(
            "📑 رتّب الشيتات حسب الأولوية المطلوبة للبحث (سيتم جلب البيانات من الشيت الأول، والمتبقي من الشيت الثاني وهكذا):",
            options=sheet_names,
            default=sheet_names
        )

        if not selected_sheets_order:
            st.warning("⚠️ يرجى اختيار شيت واحد على الأقل من ملف المصدر للبدء.")
        else:
            # معاينة الأعمدة من أول شيت لتسهيل الاختيار
            sample_sheet = excel_sheets["Sheet1"] if source_file.name.endswith('.csv') else pd.read_excel(xls_source, sheet_name=selected_sheets_order[0], nrows=5)

            cfg_col1, cfg_col2 = st.columns(2)

            with cfg_col1:
                target_key = st.selectbox("اختر عمود البحث (الـ Key/رقم الطلب) في الشيت الأساسي:", df_target.columns)
            
            with cfg_col2:
                source_key = st.selectbox("اختر عمود البحث (الـ Key/رقم الطلب) في شيت المصدر:", sample_sheet.columns)

            st.markdown("---")
            st.subheader("📅 تصفية التكرار داخل الشيت الواحد حسب أحدث تاريخ")
            
            use_date_sort = st.checkbox("تفعيل التصفية حسب أحدث تاريخ (في حالة تكرار رقم الطلب داخل الشيت)", value=True)
            
            date_col = None
            if use_date_sort:
                date_col = st.selectbox(
                    "اختر عمود التاريخ في شيت المصدر:",
                    options=sample_sheet.columns
                )

            available_columns = [col for col in sample_sheet.columns if col != source_key]
            selected_columns = st.multiselect(
                "📌 اختر الأعمدة المراد جلبها إلى الشيت الأساسي:",
                options=available_columns,
                default=available_columns[:1] if available_columns else []
            )

            if selected_columns:
                if st.button("🚀 تنفيذ عملية الدمج بحسب الأولوية الصارمة"):
                    with st.spinner("جاري جلب البيانات من الشيتات بالترتيب..."):
                        
                        # إنشاء نسخة من الشيت الأساسي للعمل عليها
                        final_df = df_target.copy()
                        
                        # إضافة الأعمدة الجديدة فارغة في البداية
                        for col in selected_columns:
                            if col not in final_df.columns:
                                final_df[col] = None

                        # معالجة الشيتات شيت تلو الآخر حسب ترتيب الأولوية
                        for sheet_name in selected_sheets_order:
                            # قراءة الشيت الحالي
                            if source_file.name.endswith('.csv'):
                                df_curr = excel_sheets["Sheet1"].copy()
                            else:
                                df_curr = pd.read_excel(xls_source, sheet_name=sheet_name)

                            if source_key not in df_curr.columns:
                                continue

                            cols_to_extract = [source_key] + [c for c in selected_columns if c in df_curr.columns]
                            if use_date_sort and date_col and date_col in df_curr.columns:
                                cols_to_extract.append(date_col)

                            df_sub = df_curr[cols_to_extract].copy()

                            # فرز حسب أحدث تاريخ داخل الشيت الحالي
                            if use_date_sort and date_col and date_col in df_sub.columns:
                                df_sub[date_col] = pd.to_datetime(df_sub[date_col], errors='coerce')
                                df_sub = df_sub.sort_values(by=date_col, ascending=False)

                            # حذف التكرار داخل الشيت نفسه
                            df_sub = df_sub.drop_duplicates(subset=[source_key], keep='first')

                            # دمج البيانات المتاحة مع الجدول الأساسي
                            merged_temp = pd.merge(
                                final_df[[target_key]], 
                                df_sub, 
                                left_on=target_key, 
                                right_on=source_key, 
                                how='left'
                            )

                            # تعبئة القيم الفارغة فقط من الشيت الحالي (دون المساس بالبيانات المجلوبة من الشيتات السابقة)
                            for col in selected_columns:
                                if col in merged_temp.columns:
                                    final_df[col] = final_df[col].fillna(merged_temp[col])

                    st.success(f"🎉 تم استكمال البيانات بنجاح بحسب أولوية الشيتات لـ {len(final_df)} صف!")
                    
                    st.subheader("📋 معاينة النتيجة:")
                    st.dataframe(final_df.head(20), use_container_width=True)

                    # تجهيز ملف Excel للتحميل
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        final_df.to_excel(writer, index=False, sheet_name='البيانات المدمجة')
                    excel_bytes = output.getvalue()

                    st.download_button(
                        label="📥 تحميل الشيت المدمج (Excel)",
                        data=excel_bytes,
                        file_name="vlookup_strict_priority_result.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة أو دمج الملفات: {e}")
