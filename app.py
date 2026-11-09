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

st.title("⚡ أداة مطابقة جلب البيانات (الأولوية للأحدث تاريخاً)")
st.write("جلب البيانات مع تطبيق أولوية التاريخ الأحدث أولاً عبر كل الشيتات المختارة بدون أخطاء تكرار الأعمدة.")

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
            
            # إزالة أي تكرار في أسماء الأعمدة بالشيت الأساسي
            df_target = df_target.loc[:, ~df_target.columns.duplicated()]
            
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
            "📑 اختر الشيتات المطلوبة ورتبها حسب أولوية الشيتات (تُستخدم للترتيب الثانوي في حال تساوي التواريخ):",
            options=sheet_names,
            default=sheet_names
        )

        if not selected_sheets_order:
            st.warning("⚠️ يرجى اختيار شيت واحد على الأقل من ملف المصدر للبدء.")
        else:
            # معايرة الأعمدة من أول شيت
            sample_sheet = excel_sheets["Sheet1"] if source_file.name.endswith('.csv') else pd.read_excel(xls_source, sheet_name=selected_sheets_order[0], nrows=5)
            sample_sheet = sample_sheet.loc[:, ~sample_sheet.columns.duplicated()]

            cfg_col1, cfg_col2 = st.columns(2)

            with cfg_col1:
                target_key = st.selectbox("اختر عمود البحث (الـ Key/رقم الطلب) في الشيت الأساسي:", df_target.columns)
            
            with cfg_col2:
                source_key = st.selectbox("اختر عمود البحث (الـ Key/رقم الطلب) في شيت المصدر:", sample_sheet.columns)

            st.markdown("---")
            st.subheader("📅 اختيار التاريخ كأولوية رئيسية")
            
            date_col = st.selectbox(
                "اختر عمود التاريخ في شيت المصدر (لاختيار البيانات ذات التاريخ الأحدث دائماً):",
                options=sample_sheet.columns
            )

            available_columns = [col for col in sample_sheet.columns if col != source_key and col != date_col]
            selected_columns = st.multiselect(
                "📌 اختر الأعمدة المراد جلبها إلى الشيت الأساسي:",
                options=available_columns,
                default=available_columns[:1] if available_columns else []
            )

            if selected_columns:
                if st.button("🚀 تنفيذ عملية الدمج والجلب (حسب التاريخ الأحدث)"):
                    with st.spinner("جاري دمج البيانات وفرز التاريخ الأحدث عبر الشيتات..."):
                        
                        # تجميع الشيتات المختارة في DataFrame واحد مع حفظ الترتيب
                        combined_frames = []
                        for rank, sheet_name in enumerate(selected_sheets_order):
                            if source_file.name.endswith('.csv'):
                                df_s = excel_sheets["Sheet1"].copy()
                            else:
                                df_s = pd.read_excel(xls_source, sheet_name=sheet_name)

                            df_s = df_s.loc[:, ~df_s.columns.duplicated()]

                            if source_key in df_s.columns and date_col in df_s.columns:
                                cols = [source_key, date_col] + [c for c in selected_columns if c in df_s.columns]
                                df_sub = df_s[cols].copy()
                                df_sub['__sheet_rank__'] = rank  # حفظ أولوية الشيت
                                combined_frames.append(df_sub)

                        if not combined_frames:
                            st.error("لم يتم العثور على الأعمدة المختارة داخل الشيتات المحددة.")
                        else:
                            all_source_data = pd.concat(combined_frames, ignore_index=True)

                            # تحويل عمود التاريخ إلى صيغة تاريخ حقيقية لضمان الترتيب الصحيح
                            all_source_data['__parsed_date__'] = pd.to_datetime(all_source_data[date_col], errors='coerce')

                            # الفرز: أولاً التاريخ الأحدث (ascending=False)، ثانياً أولوية الشيت (ascending=True)
                            all_source_data = all_source_data.sort_values(
                                by=['__parsed_date__', '__sheet_rank__'], 
                                ascending=[False, True]
                            )

                            # إزالة تكرار رقم الطلب والاحتفاظ بالأحدث تاريخاً
                            all_source_data = all_source_data.drop_duplicates(subset=[source_key], keep='first')

                            # دمج آمن 100% باستخدام الربط المباشر المعتمد على Map
                            final_df = df_target.copy()
                            for col in selected_columns:
                                if col in all_source_data.columns:
                                    mapping_dict = all_source_data.set_index(source_key)[col].to_dict()
                                    final_df[col] = final_df[target_key].map(mapping_dict)

                            st.success(f"🎉 تم جلب أحدث البيانات بنجاح لـ {len(final_df)} صف دون أي أخطاء!")
                            
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
                                file_name="vlookup_latest_date_result.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة أو دمج الملفات: {e}")
