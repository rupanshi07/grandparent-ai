import { useState, useEffect } from "react";
import axios from "axios";
import { useRouter } from "next/router";
import Link from "next/link";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function AddElder() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    phone_number: "",
    language: "hindi",
    call_time: "09:00",
  });
  const [contacts, setContacts] = useState([
    { name: "", phone: "", priority: 1 }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) router.push("/login");
  }, []);

  const handleSubmit = async () => {
    setError("");
    if (!form.name || !form.phone_number) {
      setError("Please fill in name and phone number");
      return;
    }
    if (!form.phone_number.startsWith("+")) {
      setError("Phone number must include country code e.g. +91XXXXXXXXXX");
      return;
    }
    const token = localStorage.getItem("token");
    if (!token) { router.push("/login"); return; }
    setLoading(true);
    try {
      await axios.post(`${API}/elders`, {
        ...form,
        family_contacts: contacts.filter(c => c.name && c.phone)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      router.push("/");
    } catch (e) {
      if (e.response?.status === 401) {
        localStorage.removeItem("token");
        router.push("/login");
        return;
      }
      setError(e.response?.data?.detail || "Failed to add elder");
    } finally {
      setLoading(false);
    }
  };

  const addContact = () => {
    setContacts([...contacts, { name: "", phone: "", priority: contacts.length + 1 }]);
  };

  const removeContact = (index) => {
    setContacts(contacts.filter((_, i) => i !== index));
  };

  const updateContact = (index, field, value) => {
    const updated = [...contacts];
    updated[index][field] = value;
    setContacts(updated);
  };

  return (
    <div style={styles.page}>

      {/* Sidebar */}
      <div style={styles.sidebar}>
        <div style={styles.logo}>
          <div style={styles.logoIcon}>GP</div>
          <div>
            <p style={styles.logoTitle}>Grandparent</p>
            <p style={styles.logoSub}>AI Companion</p>
          </div>
        </div>
        <nav style={styles.nav}>
          <Link href="/" style={{ textDecoration: "none" }}>
            <div style={styles.navItem}>
              <span style={styles.navText}>← Elders</span>
            </div>
          </Link>
        </nav>
      </div>

      {/* Main */}
      <div style={styles.main}>

        {/* Header */}
        <div style={styles.topBar}>
          <div style={styles.backRow}>
            <Link href="/" style={{ textDecoration: "none" }}>
              <button style={styles.backBtn}>
                <ArrowLeft size={15} color="#111" />
                Back
              </button>
            </Link>
            <div style={styles.divider}></div>
            <div>
              <h1 style={styles.pageTitle}>Add New Elder</h1>
              <p style={styles.pageSubtitle}>Register a new elderly family member</p>
            </div>
          </div>
        </div>

        <div style={styles.formContainer}>

          {error && <div style={styles.errorBox}>{error}</div>}

          {/* Twilio Trial Notice */}
          <div style={styles.noticeBox}>
            <span style={styles.noticeIcon}>ℹ️</span>
            <p style={styles.noticeText}>
              <strong>Trial Mode:</strong> Due to Twilio trial account restrictions,
              calls can currently only be made to pre-verified phone numbers.
              This limitation is removed on a paid Twilio account.
              Contact your admin to verify a number before adding.
            </p>
          </div>

          {/* Basic Info */}
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>Basic Information</h3>

            <div style={styles.fieldRow}>
              <div style={styles.field}>
                <label style={styles.label}>Full Name *</label>
                <input
                  type="text"
                  placeholder="Name"
                  value={form.name}
                  onChange={e => setForm({...form, name: e.target.value})}
                  style={styles.input}
                />
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Phone Number *</label>
                <input
                  type="text"
                  placeholder="+91XXXXXXXXXX"
                  value={form.phone_number}
                  onChange={e => setForm({...form, phone_number: e.target.value})}
                  style={styles.input}
                />
                <p style={styles.hint}>Include country code e.g. +91 for India</p>
              </div>
            </div>

            <div style={styles.fieldRow}>
              <div style={styles.field}>
                <label style={styles.label}>Preferred Language</label>
                <select
                  value={form.language}
                  onChange={e => setForm({...form, language: e.target.value})}
                  style={styles.select}>
                  <option value="hindi">Hindi</option>
                  <option value="english">English</option>
                  <option value="punjabi">Punjabi</option>
                </select>
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Daily Call Time</label>
                <input
                  type="time"
                  value={form.call_time}
                  onChange={e => setForm({...form, call_time: e.target.value})}
                  style={styles.input}
                />
                <p style={styles.hint}>AI will call at this time every day</p>
              </div>
            </div>
          </div>

          {/* Family Contacts */}
          <div style={styles.card}>
            <div style={styles.cardHeaderRow}>
              <h3 style={styles.cardTitle}>Family Contacts</h3>
              <button onClick={addContact} style={styles.addContactBtn}>
                <Plus size={13} color="#111" />
                Add Contact
              </button>
            </div>
            <p style={styles.cardSubtitle}>
              These people will be alerted if the elder misses calls or shows distress.
              Priority 1 is contacted first.
            </p>

            <div style={styles.contactList}>
              {contacts.map((contact, i) => (
                <div key={i} style={styles.contactRow}>
                  <div style={styles.priorityBadge}>P{contact.priority}</div>
                  <input
                    type="text"
                    placeholder="Name"
                    value={contact.name}
                    onChange={e => updateContact(i, "name", e.target.value)}
                    style={{...styles.input, flex: 1}}
                  />
                  <input
                    type="text"
                    placeholder="+91XXXXXXXXXX"
                    value={contact.phone}
                    onChange={e => updateContact(i, "phone", e.target.value)}
                    style={{...styles.input, flex: 1.5}}
                  />
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={contact.priority}
                    onChange={e => updateContact(i, "priority", parseInt(e.target.value))}
                    style={{...styles.input, width: "60px"}}
                  />
                  {contacts.length > 1 && (
                    <button onClick={() => removeContact(i)} style={styles.removeBtn}>
                      <Trash2 size={14} color="#999" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={loading}
            style={styles.submitBtn}>
            {loading ? "Adding elder..." : "Add Elder"}
          </button>

        </div>
      </div>
    </div>
  );
}

const styles = {
  page: {
    display: "flex",
    minHeight: "100vh",
    background: "#f5f5f5",
    fontFamily: "'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif",
  },
  sidebar: {
    width: "230px",
    background: "#111",
    display: "flex",
    flexDirection: "column",
    padding: "24px 0",
    position: "fixed",
    height: "100vh",
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "0 20px 24px",
    borderBottom: "1px solid #222",
    marginBottom: "16px",
  },
noticeBox: {
    background: "#fffbeb",
    border: "1px solid #f59e0b",
    borderLeft: "4px solid #f59e0b",
    borderRadius: "10px",
    padding: "12px 16px",
    marginBottom: "16px",
    display: "flex",
    alignItems: "flex-start",
    gap: "10px",
  },
  noticeIcon: {
    fontSize: "16px",
    flexShrink: 0,
    marginTop: "1px",
  },
  noticeText: {
    margin: 0,
    fontSize: "13px",
    color: "#92400e",
    lineHeight: "1.6",
  },

  logoIcon: {
    width: "38px",
    height: "38px",
    background: "white",
    borderRadius: "8px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#111",
    fontWeight: "800",
    fontSize: "13px",
  },
  logoTitle: { margin: 0, fontWeight: "700", fontSize: "14px", color: "white" },
  logoSub: { margin: 0, fontSize: "11px", color: "#555" },
  nav: { padding: "0 12px", flex: 1 },
  navItem: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px 12px",
    borderRadius: "8px",
    cursor: "pointer",
    marginBottom: "4px",
  },
  navText: { fontSize: "13px", color: "#888", textDecoration: "none" },
  main: { marginLeft: "230px", flex: 1, padding: "40px 44px" },
  topBar: {
    marginBottom: "32px",
    paddingBottom: "24px",
    borderBottom: "1px solid #e0e0e0",
  },
  backRow: { display: "flex", alignItems: "center", gap: "16px" },
  backBtn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    background: "white",
    border: "1px solid #e8e8e8",
    padding: "8px 14px",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: "600",
    color: "#111",
  },
  divider: { width: "1px", height: "32px", background: "#e0e0e0" },
  pageTitle: {
    margin: 0,
    fontSize: "24px",
    fontWeight: "800",
    color: "#111",
    letterSpacing: "-0.5px",
  },
  pageSubtitle: { margin: "3px 0 0", fontSize: "13px", color: "#aaa" },
  formContainer: { maxWidth: "720px" },
  errorBox: {
    background: "#fdf2f2",
    border: "1px solid #f5c6c6",
    color: "#c0392b",
    fontSize: "13px",
    padding: "12px 16px",
    borderRadius: "10px",
    marginBottom: "20px",
  },
  card: {
    background: "white",
    borderRadius: "14px",
    padding: "24px",
    border: "1px solid #e8e8e8",
    marginBottom: "16px",
  },
  cardHeaderRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "6px",
  },
  cardTitle: {
    margin: "0 0 16px",
    fontSize: "15px",
    fontWeight: "700",
    color: "#111",
  },
  cardSubtitle: {
    margin: "-10px 0 16px",
    fontSize: "12px",
    color: "#aaa",
    lineHeight: "1.5",
  },
  fieldRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "16px",
    marginBottom: "16px",
  },
  field: { display: "flex", flexDirection: "column" },
  label: {
    fontSize: "12px",
    fontWeight: "700",
    color: "#555",
    marginBottom: "6px",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  input: {
    border: "1px solid #e8e8e8",
    borderRadius: "8px",
    padding: "10px 12px",
    fontSize: "14px",
    color: "#111",
    outline: "none",
    background: "white",
    boxSizing: "border-box",
  },
  select: {
    border: "1px solid #e8e8e8",
    borderRadius: "8px",
    padding: "10px 12px",
    fontSize: "14px",
    color: "#111",
    outline: "none",
    background: "white",
    cursor: "pointer",
  },
  hint: { margin: "5px 0 0", fontSize: "11px", color: "#bbb" },
  addContactBtn: {
    display: "flex",
    alignItems: "center",
    gap: "5px",
    background: "white",
    border: "1px solid #e8e8e8",
    padding: "7px 12px",
    borderRadius: "7px",
    fontSize: "12px",
    fontWeight: "600",
    color: "#111",
    cursor: "pointer",
    marginBottom: "16px",
  },
  contactList: { display: "flex", flexDirection: "column", gap: "10px" },
  contactRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  priorityBadge: {
    width: "28px",
    height: "28px",
    background: "#f0f0f0",
    borderRadius: "6px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "11px",
    fontWeight: "700",
    color: "#555",
    flexShrink: 0,
  },
  removeBtn: {
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: "4px",
    display: "flex",
    alignItems: "center",
  },
  submitBtn: {
    width: "100%",
    background: "#111",
    color: "white",
    border: "none",
    padding: "14px",
    borderRadius: "10px",
    fontSize: "15px",
    fontWeight: "700",
    cursor: "pointer",
    marginTop: "8px",
  },
};