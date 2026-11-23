import streamlit as st
import pandas as pd
import io
import re
import json

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
        border: 1px solid #4A4A5A;
    }
    .stButton>button:hover {
        border-color: #00CC96;
        color: #00CC96;
    }
    </style>
""", unsafe_allow_html=True)

# ⚡ دوال الكاش السريعة لقراءة الملفات الكبيرة مرة واحدة فقط
@st.cache_data(show_spinner=False)
def load_target_file(file_bytes, file_name):
    if file_name.lower().endswith('.csv'):
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        df = pd.read_excel(io.BytesIO(file_bytes))
    df = df.loc[:, ~df.columns.duplicated()]
    df.columns = df.columns.astype(str).str.strip()
    return df

@st.cache_data(show_spinner=False)
def get_source_sheets_info(file_bytes, file_name):
    """استخراج أسماء الشيتات وهيدرات كل شيت بسرعة من الملف"""
    sheets_headers = {}
    if file_name.lower().endswith('.csv'):
        df_head = pd.read_csv(io.BytesIO(file_bytes), nrows=1)
        cols = [str(c).strip() for c in df_head.columns if not str(c).startswith('Unnamed:')]
        sheets_headers["Sheet1"] = cols
    else:
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        for s_name in xls.sheet_names:
            df_head = pd.read_excel(xls, sheet_name=s_name, nrows=1)
            cols = [str(c).strip() for c in df_head.columns if not str(c).startswith('Unnamed:')]
            sheets_headers[s_name] = cols
    return sheets_headers

@st.cache_data(show_spinner=False)
def read_specific_sheet(file_bytes, file_name, sheet_name):
    """قراءة شيت محدد وتخزينه في الكاش لعدم إعادة قراءته عند تغيير الإعدادات"""
    if file_name.lower().endswith('.csv'):
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
    df = df.loc[:, ~df.columns.duplicated()]
    df.columns = df.columns.astype(str).str.strip()
    return df

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

# 💾 الشريط الجانبي لحفظ واسترجاع الإعدادات المفضلة (Presets)
with st.sidebar:
    st.header("💾 الإعدادات المفضلة (Presets)")
    st.write("احفظ إعدادات الشيتات والأعمدة كملف لاسترجاعها بضغطة واحدة في المرات القادمة.")
    uploaded_preset = st.file_uploader("📂 استرجاع إعدادات محفوظة (.json):", type=["json"], key="preset_loader")
    preset_data = {}
    if uploaded_preset is not None:
        try:
            preset_data = json.load(uploaded_preset)
            st.success("✅ تم تحميل الإعدادات المفضلة!")
        except Exception:
            st.error("⚠️ ملف الإعدادات غير صالح.")

st.title("⚡ أداة مطابقة جلب البيانات المتعددة (Multi-File Dynamic Lookup)")
st.write("ارفع ملفاً أو عدة ملفات مصدر، رتب أولوية الشيتات، واجلب البيانات بالأحدث تاريخاً مع تحديد مصدر كل صف بدقة.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 1. الشيت الأساسي (الملف الصغير)")
    target_file = st.file_uploader(
        "ارفع الملف المراد إضافة البيانات إليه (Excel/CSV):",
        type=["xlsx", "xls", "csv"],
        key="target"
    )

with col2:
    st.subheader("📁 2. شيتات المصدر (ملف واحد أو عدة ملفات كبيرة)")
    source_files = st.file_uploader(
        "ارفع ملفاً أو أكثر من الملفات التي تحتوي على البيانات الكلية (Excel/CSV):",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        key="source"
    )

if target_file and source_files:
    try:
        with st.spinner("⚡ جاري قراءة وتجهيز جميع الملفات والشيتات (مدعوم بالتسريع الذكي)..."):
            df_target = load_target_file(target_file.getvalue(), target_file.name)

            # بناء خريطة موحدة لكل الشيتات عبر كافة الملفات المرفوعة
            # الصيغة: "[اسم الملف] -> اسم الشيت"
            sheet_registry = {}
            all_sheet_labels = []

            for s_file in source_files:
                f_bytes = s_file.getvalue()
                f_name = s_file.name
                sheets_info = get_source_sheets_info(f_bytes, f_name)
                for s_name, cols in sheets_info.items():
                    label = f"[{f_name}] -> {s_name}"
                    sheet_registry[label] = {
                        "file_bytes": f_bytes,
                        "file_name": f_name,
                        "sheet_name": s_name,
                        "headers": cols
                    }
                    all_sheet_labels.append(label)

        st.success(f"✅ تم تحميل الشيت الأساسي وعدد ({len(source_files)}) ملف مصدر بإجمالي ({len(all_sheet_labels)}) شيت!")
        st.divider()

        st.subheader("⚙️ إعدادات الشيتات والأولوية والربط")

        # تطبيق الإعدادات المفضلة إن وجدت
        default_sheets = [s for s in preset_data.get("selected_sheets_order", []) if s in all_sheet_labels]
        if not default_sheets:
            default_sheets = all_sheet_labels

        selected_sheets_order = st.multiselect(
            "📑 حدد الشيتات المطلوبة من كافة الملفات ورتبها حسب أولوية البحث (من الأعلى للأقل أولوية):",
            options=all_sheet_labels,
            default=default_sheets
        )

        if not selected_sheets_order:
            st.warning("⚠️ يرجى اختيار شيت واحد على الأقل من ملفات المصدر للبدء.")
        else:
            # تجميع كافة الهيدرات المتاحة ديناميكياً من الشيتات المختارة فقط
            all_source_headers = []
            for label in selected_sheets_order:
                for c in sheet_registry[label]["headers"]:
                    if c not in all_source_headers:
                        all_source_headers.append(c)

            cfg_col1, cfg_col2 = st.columns(2)

            target_cols_list = list(df_target.columns)
            default_t_key_idx = target_cols_list.index(preset_data["target_key"]) if preset_data.get("target_key") in target_cols_list else 0
            default_s_key_idx = all_source_headers.index(preset_data["source_key"]) if preset_data.get("source_key") in all_source_headers else 0

            with cfg_col1:
                target_key = st.selectbox(
                    "في الشيت الأساسي (رقم الطلب/Key الـ) اختر عمود البحث:",
                    target_cols_list,
                    index=default_t_key_idx
                )

            with cfg_col2:
                source_key = st.selectbox(
                    "في شيتات المصدر (رقم الطلب/Key الـ) اختر عمود البحث:",
                    all_source_headers,
                    index=default_s_key_idx
                )

            st.markdown("---")
            st.subheader("📅 اختيار عمود التاريخ للمفاضلة بالأحدث (اختياري/إلزامي)")

            date_options = ["بدون مفاضلة بالتاريخ (الاعتماد على أولوية الشيتات فقط)"] + all_source_headers
            default_date_idx = date_options.index(preset_data["date_col"]) if preset_data.get("date_col") in date_options else (1 if len(date_options) > 1 else 0)

            date_col = st.selectbox(
                "اختر عمود التاريخ في شيتات المصدر:",
                options=date_options,
                index=default_date_idx
            )

            available_columns = [col for col in all_source_headers if col != source_key]
            default_selected_cols = [c for c in preset_data.get("selected_columns", []) if c in available_columns]

            selected_columns = st.multiselect(
                "📌 اختر الهيدرات المراد جلب بياناتها إلى الشيت الأساسي:",
                options=available_columns,
                default=default_selected_cols
            )

            # خيار إضافة عمود يوضح من أي ملف وشيت تم استخراج البيانات
            include_source_tag = st.checkbox(
                "🏷️ إضافة عمود (مصدر البيانات) يوضح اسم الملف واسم الشيت الذي تم الجلب منه لكل صف",
                value=preset_data.get("include_source_tag", True)
            )

            # تحديث زر حفظ الإعدادات في الشريط الجانبي
            current_config = {
                "selected_sheets_order": selected_sheets_order,
                "target_key": target_key,
                "source_key": source_key,
                "date_col": date_col,
                "selected_columns": selected_columns,
                "include_source_tag": include_source_tag
            }
            with st.sidebar:
                st.divider()
                st.download_button(
                    label="💾 تنزيل الإعدادات الحالية كملف مفضل",
                    data=json.dumps(current_config, ensure_ascii=False, indent=2),
                    file_name="vlookup_preset.json",
                    mime="application/json"
                )

            if selected_columns or include_source_tag:
                if st.button("🚀 تنفيذ عملية البحث والجلب الديناميكي (Dynamic VLOOKUP)"):
                    with st.spinner("جاري فحص الهيدرات وجلب البيانات من كافة الملفات والشيتات..."):
                        combined_frames = []
                        use_date = date_col != "بدون مفاضلة بالتاريخ (الاعتماد على أولوية الشيتات فقط)"

                        for rank, label in enumerate(selected_sheets_order):
                            info = sheet_registry[label]
                            df_s = read_specific_sheet(info["file_bytes"], info["file_name"], info["sheet_name"]).copy()

                            if source_key in df_s.columns:
                                df_s['__clean_key__'] = clean_key_series(df_s[source_key])
                                # استبعاد المفاتيح الفارغة تماماً
                                df_s = df_s[df_s['__clean_key__'] != ""]

                                cols_to_read = ['__clean_key__']
                                if use_date and date_col in df_s.columns:
                                    cols_to_read.append(date_col)

                                for c in selected_columns:
                                    if c in df_s.columns and c not in cols_to_read:
                                        cols_to_read.append(c)

                                df_sub = df_s[cols_to_read].copy()
                                df_sub['__sheet_rank__'] = rank
                                df_sub['__source_origin__'] = label
                                combined_frames.append(df_sub)

                        if not combined_frames:
                            st.error("⚠️ لم يتم العثور على عمود المفتاح في أي من الشيتات المختارة!")
                        else:
                            all_source_data = pd.concat(combined_frames, ignore_index=True)

                            # الترتيب حسب التاريخ الأحدث أولاً (إن وجد)، ثم حسب أولوية ترتيب الشيتات
                            if use_date and date_col in all_source_data.columns:
                                all_source_data['__parsed_date__'] = pd.to_datetime(all_source_data[date_col], errors='coerce')
                                all_source_data = all_source_data.sort_values(
                                    by=['__parsed_date__', '__sheet_rank__'],
                                    ascending=[False, True],
                                    na_position='last'
                                )
                            else:
                                all_source_data = all_source_data.sort_values(by='__sheet_rank__', ascending=True)

                            # الاحتفاظ بأول ظهور (الأحدث تاريخاً والأعلى أولوية)
                            all_source_data = all_source_data.drop_duplicates(subset=['__clean_key__'], keep='first')

                            # المطابقة والجلب للشيت الأساسي
                            final_df = df_target.copy()
                            clean_target_keys = clean_key_series(final_df[target_key])

                            for col in selected_columns:
                                if col in all_source_data.columns:
                                    mapping_dict = all_source_data.set_index('__clean_key__')[col].to_dict()
                                    final_df[col] = clean_target_keys.map(mapping_dict)

                            # إضافة عمود مصدر البيانات الدقيق
                            origin_dict = all_source_data.set_index('__clean_key__')['__source_origin__'].to_dict()
                            mapped_origin = clean_target_keys.map(origin_dict).fillna("غير موجود")
                            if include_source_tag:
                                final_df["مصدر البيانات (الملف -> الشيت)"] = mapped_origin

                    # عرض إحصائيات سريعة
                    matched_count = (mapped_origin != "غير موجود").sum()
                    unmatched_count = (mapped_origin == "غير موجود").sum()

                    st.success(f"🎉 تم الانتهاء بنجاح! تم العثور على **{matched_count}** صف، ولم يتم العثور على **{unmatched_count}** صف.")

                    st.subheader("📋 معاينة النتيجة (أول 20 صف):")
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
