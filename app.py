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

st.title("⚡ أداة مطابقة جلب البيانات السريعة (VLOOKUP الفائق)")
st.write("ربط جلب عدة أعمدة من شيت كبير إلى شيت آخر بسرعة فائقة.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 1. الشيت الأساسي (الملف الصغير)")
    target_file = st.file_uploader("ارفع الملف المراد إضافة البيانات إليه (Excel/CSV):", type=["xlsx", "xls", "csv"], key="target")

with col2:
    st.subheader("📁 2. شيت المصدر (الملف الكبير)")
    source_file = st.file_uploader("ارفع الملف الذي يحتوي على البيانات الكلية (Excel/CSV):", type=["xlsx", "xls", "csv"], key="source")

if target_file and source_file:
    try:
        # قراءة الملفات
        with st.spinner("جاري قراءة البيانات..."):
            df_target = pd.read_csv(target_file) if target_file.name.endswith('.csv') else pd.read_excel(target_file)
            df_source = pd.read_csv(source_file) if source_file.name.endswith('.csv') else pd.read_excel(source_file)

        st.success("✅ تم تحميل الملفين بنجاح!")
        st.divider()

        st.subheader("⚙️ إعدادات الربط واستخراج البيانات")
        
        cfg_col1, cfg_col2 = st.columns(2)

        with cfg_col1:
            target_key = st.selectbox("اختر عمود البحث (الـ Key) في الشيت الأساسي:", df_target.columns)
        
        with cfg_col2:
            source_key = st.selectbox("اختر عمود البحث (الـ Key) في شيت المصدر الكلي:", df_source.columns)

        # اختيار الأعمدة المراد نقلها من الشيت الكبير
        available_columns = [col for col in df_source.columns if col != source_key]
        selected_columns = st.multiselect(
            "📌 اختر الأعمدة المراد جلبها من شيت المصدر إلى الشيت الأساسي:",
            options=available_columns,
            default=available_columns[:1] if available_columns else []
        )

        if selected_columns:
            if st.button("🚀 تنفيذ عملية الدمج والجلب الفوري"):
                with st.spinner("جاري معالجة وربط البيانات بسرعة..."):
                    # تجهيز البيانات للدمج الفائق
                    cols_to_fetch = [source_key] + selected_columns
                    df_source_filtered = df_source[cols_to_fetch].drop_duplicates(subset=[source_key])

                    # عملية الدمج المباشر (VLOOKUP الفائق)
                    merged_df = pd.merge(
                        df_target,
                        df_source_filtered,
                        left_on=target_key,
                        right_on=source_key,
                        how='left'
                    )

                    # إذا كان عمود الربط مختلف في الاسم يمسح التكرار
                    if target_key != source_key and source_key in merged_df.columns:
                        merged_df.drop(columns=[source_key], inplace=True)

                st.success(f"🎉 تم جلب {len(selected_columns)} أعمدة بنجاح لـ {len(merged_df)} صف!")
                
                st.subheader("📋 معاينة النتيجة:")
                st.dataframe(merged_df.head(20), use_container_width=True)

                # تجهيز شيت Excel للتحميل
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    merged_df.to_excel(writer, index=False, sheet_name='البيانات المدمجة')
                excel_bytes = output.getvalue()

                st.download_button(
                    label="📥 تحميل الشيت المدمج (Excel)",
                    data=excel_bytes,
                    file_name="vlookup_result.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة أو دمج الملفات: {e}")
