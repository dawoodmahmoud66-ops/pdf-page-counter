import streamlit as st
import pandas as pd
import io
import re

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

st.title("⚡ أداة مطابقة جلب البيانات (Dynamic Header Lookup)")
st.write("البحث الذكي عن اسم الهيدر عبر كافة الشيتات وجلب البيانات بالأحدث تاريخاً بغض النظر عن ترتيب الأعمدة.")

st.divider()

def clean_key_series(series):
    """دالة لقص المسافات وإزالة .0 وتحويل الأرقام لنصوص مطابقة 100%"""
    def clean_val(val):
        if pd.isna(val):
            return ""
        s = str(val).strip()
        if s.endswith('.0'):
            s = s[:-2]
        s = re.sub(r'\s+', '', s)
        return s
    return series.apply(clean_val)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 1. الشيت الأساسي (الملف الصغير)")
    target_file = st.file_uploader("ارفع الملف المراد إضافة البيانات إليه (Excel/CSV):", type=["xlsx", "xls", "csv"], key="target")

with col2:
    st.subheader("📁 2. شيت المصدر (الملف الكبير المتعدد الشيتات)")
    source_file = st.file_uploader("ارفع الملف الذي يحتوي على البيانات الكلية (Excel/CSV):", type=["xlsx", "xls", "csv"], key="source")

if target_file and source_file:
    try:
        with st.spinner("جاري قراءة وتجهيز جميع الشيتات وقراءة الهيدرات..."):
            df_target = pd.read_csv(target_file) if target_file.name.endswith('.csv') else pd.read_excel(target_file)
            df_target = df_target.loc[:, ~df_target.columns.duplicated()]
            df_target.columns = df_target.columns.astype(str).str.strip()

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
            "📑 حدد الشيتات المطلوبة ورتبها حسب أولوية البحث:",
            options=sheet_names,
            default=sheet_names
        )

        if not selected_sheets_order:
            st.warning("⚠️ يرجى اختيار شيت واحد على الأقل من ملف المصدر للبدء.")
        else:
            # مسح الهيدرات المتاحة ديناميكياً من كافة الشيتات المختارة
            all_source_headers = []
            for s_name in selected_sheets_order:
                if source_file.name.endswith('.csv'):
                    cols = excel_sheets["Sheet1"].columns.astype(str).str.strip().tolist()
                else:
                    cols = pd.read_excel(xls_source, sheet_name=s_name, nrows=1).columns.astype(str).str.strip().tolist()
                for c in cols:
                    if c not in all_source_headers and not c.startswith('Unnamed:'):
                        all_source_headers.append(c)

            cfg_col1, cfg_col2 = st.columns(2)

            with cfg_col1:
                target_key = st.selectbox("اختر عمود البحث (الـ Key/رقم الطلب) في الشيت الأساسي:", df_target.columns)
            
            with cfg_col2:
                source_key = st.selectbox("اختر عمود البحث (الـ Key/رقم الطلب) في شيت المصدر:", all_source_headers)

            st.markdown("---")
            st.subheader("📅 اختيار عمود التاريخ للمفاضلة بالأحدث")
            
            date_col = st.selectbox(
                "اختر عمود التاريخ في شيت المصدر:",
                options=all_source_headers
            )

            available_columns = [col for col in all_source_headers if col != source_key]
            
            selected_columns = st.multiselect(
                "📌 اختر الهيدرات المراد جلب بياناتها إلى الشيت الأساسي:",
                options=available_columns,
                default=[]
            )

            if selected_columns:
                if st.button("🚀 تنفيذ عملية البحث والجلب الديناميكي (Dynamic VLOOKUP)"):
                    with st.spinner("جاري فحص الهيدرات وجلب البيانات من كل الشيتات بالأحدث تاريخاً..."):
                        
                        combined_frames = []
                        
                        # المرور على كل شيت وقراءة الهيدرات الموجودة فيه فقط
                        for rank, sheet_name in enumerate(selected_sheets_order):
                            if source_file.name.endswith('.csv'):
                                df_s = excel_sheets["Sheet1"].copy()
                            else:
                                df_s = pd.read_excel(xls_source, sheet_name=sheet_name)

                            df_s = df_s.loc[:, ~df_s.columns.duplicated()]
                            df_s.columns = df_s.columns.astype(str).str.strip()

                            # التأكد من وجود عمود المفتاح في هذا الشيت
                            if source_key in df_s.columns:
                                df_s['__clean_key__'] = clean_key_series(df_s[source_key])
                                
                                cols_to_read = ['__clean_key__']
                                if date_col in df_s.columns:
                                    cols_to_read.append(date_col)
                                
                                # البحث الديناميكي عن الهيدرات المختارة
                                for c in selected_columns:
                                    if c in df_s.columns and c not in cols_to_read:
                                        cols_to_read.append(c)
                                        
                                df_sub = df_s[cols_to_read].copy()
                                df_sub['__sheet_rank__'] = rank
                                combined_frames.append(df_sub)

                        if not combined_frames:
                            st.error("لم يتم العثور على عمود المفتاح في أي شيت!")
                        else:
                            all_source_data = pd.concat(combined_frames, ignore_index=True)

                            # الترتيب حسب التاريخ الأحدث أولاً، ثم حسب أولوية ترتيب الشيتات
                            if date_col in all_source_data.columns:
                                all_source_data['__parsed_date__'] = pd.to_datetime(all_source_data[date_col], errors='coerce')
                                all_source_data = all_source_data.sort_values(
                                    by=['__parsed_date__', '__sheet_rank__'], 
                                    ascending=[False, True]
                                )
                            else:
                                all_source_data = all_source_data.sort_values(by='__sheet_rank__', ascending=True)

                            # احتفاظ بأول ظهور (الأحدث تاريخاً)
                            all_source_data = all_source_data.drop_duplicates(subset=['__clean_key__'], keep='first')

                            # المطابقة والجلب للشيت الأساسي
                            final_df = df_target.copy()
                            clean_target_keys = clean_key_series(final_df[target_key])

                            for col in selected_columns:
                                if col in all_source_data.columns:
                                    mapping_dict = all_source_data.set_index('__clean_key__')[col].to_dict()
                                    final_df[col] = clean_target_keys.map(mapping_dict)

                    st.success(f"🎉 تم جلب البيانات بنجاح من جميع الشيتات لـ {len(final_df)} صف!")
                    
                    st.subheader("📋 معاينة النتيجة:")
                    st.dataframe(final_df.head(20), use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        final_df.to_excel(writer, index=False, sheet_name='البيانات المدمجة')
                    excel_bytes = output.getvalue()

                    st.download_button(
                        label="📥 تحميل الشيت المدمج (Excel)",
                        data=excel_bytes,
                        file_name="dynamic_vlookup_result.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة أو دمج الملفات: {e}")
