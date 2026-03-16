import streamlit as st
import json
import re
import os
from datetime import datetime

# --- CONFIGURATION ---
PASSWORD = "odongo2735"
SETTINGS_FILE = "settings.json"
AUDIT_LOG_FILE = "audit_log.json"


# --- CUSTOM CSS STYLING ---
def load_custom_css():
    st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }

    /* Container Cards */
    .css-1r6slb0 {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 0.9em;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        color: white;
    }
    .css-1d391kg .stSelectbox > label {
        color: white;
    }

    /* Headers */
    h1, h2, h3 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }

    /* Success/Error Messages */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }

    /* Dataframe */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }

    /* Input Fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: border-color 0.3s ease;
    }
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #667eea;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.9em;
    }

    /* Settings Item Card */
    .setting-item {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
    }
    </style>
    """, unsafe_allow_html=True)


# --- VALIDATION RULES ---
VALIDATION_RULES = {
    "volume": {"type": "Integer", "min": 0, "max": 100, "error": "Volume must be between 0 and 100"},
    "email": {"type": "String", "pattern": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
              "error": "Invalid email format"},
    "theme": {"type": "String", "allowed": ["dark", "light", "auto"],
              "error": "Theme must be 'dark', 'light', or 'auto'"},
    "font_size": {"type": "Integer", "min": 10, "max": 72, "error": "Font size must be between 10 and 72"},
    "session_timeout": {"type": "Integer", "min": 5, "max": 1440,
                        "error": "Session timeout must be between 5 and 1440 minutes"},
    "cache_size_mb": {"type": "Integer", "min": 100, "max": 5000,
                      "error": "Cache size must be between 100 and 5000 MB"},
    "language": {"type": "String", "allowed": ["en", "es", "fr", "de", "ja", "zh"], "error": "Invalid language code"},
    "password": {"type": "String", "min_length": 8, "error": "Password must be at least 8 characters"}
}

# --- DEFAULT SETTINGS ---
DEFAULT_SETTINGS = {
    "theme": "dark",
    "language": "en",
    "font_size": 14,
    "compact_mode": True,
    "timezone": "UTC",
    "date_format": "MM/DD/YYYY",
    "email_notifications": True,
    "push_notifications": False,
    "notification_sound": True,
    "digest_frequency": "weekly",
    "marketing_emails": False,
    "two_factor_auth": False,
    "session_timeout": 30,
    "data_sharing": False,
    "public_profile": True,
    "show_online_status": True,
    "auto_save": True,
    "auto_update": True,
    "cache_size_mb": 500,
    "image_quality": "high",
    "download_path": "/Downloads"
}


# --- HELPER FUNCTIONS ---
def parse_value(value, value_type):
    if value_type == "Boolean":
        return value.lower() in ['true', 'yes', '1', 'on']
    elif value_type == "Integer":
        try:
            return int(value)
        except ValueError:
            return None
    elif value_type == "Float":
        try:
            return float(value)
        except ValueError:
            return None
    else:
        return str(value)


def get_type_name(value):
    if isinstance(value, bool):
        return "Boolean"
    elif isinstance(value, int):
        return "Integer"
    elif isinstance(value, float):
        return "Float"
    else:
        return "String"


def get_type_icon(value_type):
    icons = {"Boolean": "🔘", "Integer": "🔢", "Float": "📊", "String": "📝"}
    return icons.get(value_type, "📌")


def get_action_icon(action):
    icons = {"ADD": "➕", "UPDATE": "✏️", "DELETE": "🗑️", "RESET": "🔄", "IMPORT": "📤"}
    return icons.get(action, "📋")


# --- LOGIC CLASS ---
class SettingsManager:
    def __init__(self, filename=SETTINGS_FILE, log_file=AUDIT_LOG_FILE):
        self.filename = filename
        self.log_file = log_file
        self.settings = self.load()
        self.audit_log = self.load_log()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return DEFAULT_SETTINGS.copy()
        return DEFAULT_SETTINGS.copy()

    def load_log(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save(self):
        with open(self.filename, 'w') as f: json.dump(self.settings, f, indent=4)

    def save_log(self):
        with open(self.log_file, 'w') as f: json.dump(self.audit_log, f, indent=4)

    def log_action(self, action, key, details=""):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "key": key,
            "details": details
        }
        self.audit_log.insert(0, entry)
        if len(self.audit_log) > 50: self.audit_log.pop()
        self.save_log()

    def validate_setting(self, key, value, value_type):
        key_lower = key.lower()
        if key_lower not in VALIDATION_RULES:
            return True, "OK"
        rules = VALIDATION_RULES[key_lower]
        if rules.get("type") != value_type:
            return False, f"Expected type: {rules['type']}"
        if value_type in ["Integer", "Float"]:
            num_value = parse_value(value, value_type)
            if num_value is None:
                return False, "Invalid number"
            if "min" in rules and num_value < rules["min"]:
                return False, rules.get("error", f"Value must be >= {rules['min']}")
            if "max" in rules and num_value > rules["max"]:
                return False, rules.get("error", f"Value must be <= {rules['max']}")
        if "allowed" in rules:
            if value.lower() not in [a.lower() for a in rules["allowed"]]:
                return False, rules.get("error", f"Must be one of: {rules['allowed']}")
        if "pattern" in rules:
            if not re.match(rules["pattern"], value):
                return False, rules.get("error", "Invalid format")
        if "min_length" in rules:
            if len(value) < rules["min_length"]:
                return False, rules.get("error", f"Must be at least {rules['min_length']} characters")
        return True, "Valid"

    def add_setting(self, key, value, value_type="String"):
        key_lower = str(key).lower()
        if key_lower in self.settings:
            return False, f"Setting '{key_lower}' already exists!"
        is_valid, message = self.validate_setting(key, value, value_type)
        if not is_valid:
            return False, f"Validation failed: {message}"
        parsed_value = parse_value(value, value_type)
        if parsed_value is None and value_type in ["Integer", "Float"]:
            return False, f"Invalid {value_type} value!"
        self.settings[key_lower] = parsed_value
        self.save()
        self.log_action("ADD", key_lower, f"Type: {value_type}, Value: {parsed_value}")
        return True, f"Setting '{key_lower}' added successfully!"

    def update_setting(self, key, value, value_type="String"):
        key_lower = str(key).lower()
        if key_lower not in self.settings:
            return False, f"Setting '{key_lower}' does not exist!"
        is_valid, message = self.validate_setting(key, value, value_type)
        if not is_valid:
            return False, f"Validation failed: {message}"
        old_value = self.settings[key_lower]
        parsed_value = parse_value(value, value_type)
        if parsed_value is None and value_type in ["Integer", "Float"]:
            return False, f"Invalid {value_type} value!"
        self.settings[key_lower] = parsed_value
        self.save()
        self.log_action("UPDATE", key_lower, f"{old_value} -> {parsed_value}")
        return True, f"Setting '{key_lower}' updated successfully!"

    def delete_setting(self, key):
        key_lower = str(key).lower()
        if key_lower in self.settings:
            del self.settings[key_lower]
            self.save()
            self.log_action("DELETE", key_lower)
            return True, f"Setting '{key_lower}' deleted successfully!"
        return False, "Setting not found!"

    def reset_to_defaults(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.save()
        self.log_action("RESET", "ALL", "Restored defaults")
        return True, "All settings reset to defaults!"

    def import_settings(self, uploaded_data):
        try:
            data = json.load(uploaded_data)
            if not isinstance(data, dict):
                return False, "Invalid JSON structure."
            self.settings = data
            self.save()
            self.log_action("IMPORT", "FILE", "Settings imported from upload")
            return True, "Settings imported successfully!"
        except Exception as e:
            return False, f"Import failed: {str(e)}"

    def get_settings_summary(self):
        return {
            "total": len(self.settings),
            "booleans": sum(1 for v in self.settings.values() if isinstance(v, bool)),
            "numbers": sum(1 for v in self.settings.values() if isinstance(v, (int, float))),
            "strings": sum(1 for v in self.settings.values() if isinstance(v, str)),
            "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# --- AUTHENTICATION ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.markdown("<h1 style='text-align: center; color: white;'>🔐 Secure Login</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: rgba(255,255,255,0.9);'>Enter your password to access the Settings Manager</p>",
        unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Password", type="password", placeholder="Enter password...",
                                 label_visibility="collapsed")
        if st.button("🔓 Unlock Dashboard", use_container_width=True):
            if password == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect password!")
    return False


def logout():
    st.session_state.authenticated = False
    st.rerun()


# --- UI COMPONENTS ---
def render_metric_card(label, value, icon):
    return f"""
    <div class="metric-card">
        <div style="font-size: 2em;">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def render_setting_item(key, value, value_type):
    icon = get_type_icon(value_type)
    status = "✅" if value else "❌" if isinstance(value, bool) else ""
    return f"""
    <div class="setting-item">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong style="color: #667eea;">{icon} {key}</strong>
                <div style="color: #666; font-size: 0.9em; margin-top: 5px;">Value: {value} {status}</div>
            </div>
            <div style="background: #f0f0f0; padding: 5px 10px; border-radius: 5px; font-size: 0.8em;">
                {value_type}
            </div>
        </div>
    </div>
    """


# --- WEB INTERFACE ---
def main():
    st.set_page_config(page_title="⚙️ Settings Manager", page_icon="🎨", layout="wide")
    load_custom_css()

    if not check_password():
        st.markdown("<div class='footer'>🔒 Secure Settings Manager | Powered by Streamlit & Python</div>",
                    unsafe_allow_html=True)
        return

    with st.sidebar:
        st.markdown("<h2 style='color: white; text-align: center;'>⚙️ Navigation</h2>", unsafe_allow_html=True)
        st.markdown("---")
        action = st.selectbox("Choose Action",
                              ["📋 View Settings", "➕ Add Setting", "✏️ Update Setting", "🗑️ Delete Setting",
                               "📤 Import Settings", "🔄 Reset to Defaults", "📜 Audit Log"])
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
        st.markdown(
            "<div style='text-align: center; color: rgba(255,255,255,0.6); font-size: 0.8em; margin-top: 20px;'>v2.0 Professional</div>",
            unsafe_allow_html=True)

    # Header
    st.markdown(
        "<h1 style='text-align: center; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>⚙️ Settings Management Dashboard</h1>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: rgba(255,255,255,0.9); font-size: 1.1em;'>Manage your application configuration with style & precision</p>",
        unsafe_allow_html=True)
    st.markdown("---")

    if 'manager' not in st.session_state:
        st.session_state.manager = SettingsManager()
    manager = st.session_state.manager
    summary = manager.get_settings_summary()

    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_metric_card("Total Settings", summary["total"], "📊"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card("Booleans", summary["booleans"], "🔘"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card("Numbers", summary["numbers"], "🔢"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_metric_card("Strings", summary["strings"], "📝"), unsafe_allow_html=True)

    st.markdown("---")

    # --- VIEW SETTINGS ---
    if action == "📋 View Settings":
        st.markdown("<h2>📋 Current Configuration</h2>", unsafe_allow_html=True)
        search_term = st.text_input("🔍 Search Settings...", placeholder="Type to filter settings...")

        display_settings = manager.settings
        if search_term:
            display_settings = {k: v for k, v in manager.settings.items() if search_term.lower() in k.lower()}
            if display_settings:
                st.success(f"✅ Found {len(display_settings)} settings matching '{search_term}'")
            else:
                st.warning(f"⚠️ No settings found matching '{search_term}'")

        if not display_settings:
            st.info("📭 No settings available. Add some or reset to defaults!")
        else:
            # Organize by type with cards
            bool_settings = {k: v for k, v in display_settings.items() if isinstance(v, bool)}
            num_settings = {k: v for k, v in display_settings.items() if isinstance(v, (int, float))}
            str_settings = {k: v for k, v in display_settings.items() if isinstance(v, str)}

            if bool_settings:
                st.markdown("### 🔘 Boolean Settings")
                for k, v in bool_settings.items():
                    st.markdown(render_setting_item(k, v, "Boolean"), unsafe_allow_html=True)

            if num_settings:
                st.markdown("### 🔢 Numeric Settings")
                for k, v in num_settings.items():
                    st.markdown(render_setting_item(k, v, get_type_name(v)), unsafe_allow_html=True)

            if str_settings:
                st.markdown("### 📝 String Settings")
                for k, v in str_settings.items():
                    st.markdown(render_setting_item(k, v, "String"), unsafe_allow_html=True)

            st.markdown("---")
            json_str = json.dumps(manager.settings, indent=4)
            st.download_button(
                label="📥 Download Settings Backup",
                data=json_str,
                file_name=f"settings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    # --- ADD SETTING ---
    elif action == "➕ Add Setting":
        st.markdown("<h2>➕ Add New Setting</h2>", unsafe_allow_html=True)
        with st.form("add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                key = st.text_input("Setting Key", placeholder="e.g., max_users")
            with col2:
                value_type = st.selectbox("Data Type", ["String", "Boolean", "Integer", "Float"])

            # Show validation hints
            if key and key.lower() in VALIDATION_RULES:
                rule = VALIDATION_RULES[key.lower()]
                st.info(f"📋 **Validation Rules:** {rule.get('error', 'See documentation')}")

            value = st.text_input("Setting Value", placeholder="Enter value...")
            submitted = st.form_submit_button("💾 Add Setting", use_container_width=True)

            if submitted:
                if not key or not value:
                    st.error("❌ Both Key and Value are required!")
                else:
                    success, msg = manager.add_setting(key, value, value_type)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # --- UPDATE SETTING ---
    elif action == "✏️ Update Setting":
        st.markdown("<h2>✏️ Update Existing Setting</h2>", unsafe_allow_html=True)
        if not manager.settings:
            st.warning("⚠️ No settings to update. Add some first!")
        else:
            with st.form("update_form"):
                selected_key = st.selectbox("Select Setting", list(manager.settings.keys()))
                current_value = manager.settings[selected_key]
                current_type = get_type_name(current_value)

                st.info(f"📌 **Current Value:** `{current_value}` | **Type:** {current_type}")

                if selected_key.lower() in VALIDATION_RULES:
                    rule = VALIDATION_RULES[selected_key.lower()]
                    st.warning(f"⚠️ **Validation Rules:** {rule.get('error', 'See documentation')}")

                value_type = st.selectbox("Data Type", ["String", "Boolean", "Integer", "Float"],
                                          index=["String", "Boolean", "Integer", "Float"].index(current_type))
                value = st.text_input("New Value", value=str(current_value))

                submitted = st.form_submit_button("✏️ Update Setting", use_container_width=True)

                if submitted:
                    success, msg = manager.update_setting(selected_key, value, value_type)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # --- DELETE SETTING ---
    elif action == "🗑️ Delete Setting":
        st.markdown("<h2>🗑️ Delete Setting</h2>", unsafe_allow_html=True)
        if not manager.settings:
            st.warning("⚠️ No settings to delete.")
        else:
            keys_list = list(manager.settings.keys())
            key_to_delete = st.selectbox("Select Setting to Delete", keys_list)

            current_value = manager.settings[key_to_delete]
            st.error(f"⚠️ **Warning:** You are about to delete **`{key_to_delete}`** with value **`{current_value}`**")

            confirm = st.checkbox("I understand this action cannot be undone")
            if st.button("🗑️ Confirm Delete", use_container_width=True, disabled=not confirm):
                success, msg = manager.delete_setting(key_to_delete)
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    # --- IMPORT SETTINGS ---
    elif action == "📤 Import Settings":
        st.markdown("<h2>📤 Import Settings from File</h2>", unsafe_allow_html=True)
        st.warning("⚠️ **Warning:** This will overwrite all current settings! Make sure to backup first.")

        uploaded_file = st.file_uploader("📁 Choose a JSON file", type="json")

        if uploaded_file is not None:
            st.info(f"📄 Selected: **{uploaded_file.name}**")
            if st.button("📤 Upload & Import", use_container_width=True):
                success, msg = manager.import_settings(uploaded_file)
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    # --- RESET TO DEFAULTS ---
    elif action == "🔄 Reset to Defaults":
        st.markdown("<h2>🔄 Reset All Settings</h2>", unsafe_allow_html=True)
        st.error("⚠️ **Warning:** This will delete all custom settings and restore factory defaults!")

        st.markdown("### Default Settings Preview:")
        st.json(DEFAULT_SETTINGS)

        confirm = st.checkbox("I understand all custom settings will be lost")
        if st.button("🔄 Confirm Reset", use_container_width=True, disabled=not confirm, type="secondary"):
            success, msg = manager.reset_to_defaults()
            if success:
                st.success(f"✅ {msg}")
                st.rerun()

    # --- AUDIT LOG ---
    elif action == "📜 Audit Log":
        st.markdown("<h2>📜 Activity Audit Log</h2>", unsafe_allow_html=True)
        if not manager.audit_log:
            st.info("📭 No activity recorded yet.")
        else:
            # Style the dataframe
            st.dataframe(
                manager.audit_log,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "timestamp": "🕐 Timestamp",
                    "action": "🔧 Action",
                    "key": "📌 Setting Key",
                    "details": "📝 Details"
                }
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear Log", use_container_width=True):
                    manager.audit_log = []
                    manager.save_log()
                    st.rerun()
            with col2:
                log_json = json.dumps(manager.audit_log, indent=4)
                st.download_button(
                    label="📥 Download Log",
                    data=log_json,
                    file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'>🔒 Secure Settings Manager v2.0 | Built with ❤️ using Streamlit & Python</div>",
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()