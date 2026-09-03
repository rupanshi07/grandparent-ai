import { useState, useEffect } from "react";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/router";
import { ArrowLeft, Phone, Clock, Globe, 
         Users, Bell, Brain, Calendar } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function ElderDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [elder, setElder] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newTime, setNewTime] = useState("09:00");

    useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { router.push("/login"); return; }
    if (id) { fetchElder(); fetchAlerts(); }
  }, [id]);

    const fetchElder = async () => {
    const token = localStorage.getItem("token");
    if (!token) { router.push("/login"); return; }
    try {
      const res = await axios.get(`${API}/elders/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setElder(res.data);
      setNewTime(res.data.call_time);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

    const fetchAlerts = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const res = await axios.get(`${API}/elders/${id}/alerts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAlerts(res.data.alerts);
    } catch (e) { console.error(e); }
  };

    const updateCallTime = async (newTime) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try:
      await axios.patch(`${API}/elders/${id}/schedule`, {
        call_time: newTime
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert(`Call time updated to ${newTime}!`);
      fetchElder();
    } catch (e) { alert("Failed to update schedule"); }
  };

  const getAlertBorder = (level) => {
    switch (level) {
      case "CRITICAL": return "2px solid #111";
      case "HIGH": return "1px solid #555";
      default: return "1px solid #e8e8e8";
    }
  };

  const getAlertIcon = (level) => {
    switch (level) {
      case "CRITICAL": return "🚨";
      case "HIGH": return "⚠️";
      case "MEDIUM": return "🔔";
      default: return "ℹ️";
    }
  };

  if (loading) return (
    <div style={styles.loading}>
      <p style={{ color: "#aaa", fontSize: "14px" }}>Loading...</p>
    </div>
  );

  if (!elder) return (
    <div style={styles.loading}>
      <p style={{ color: "#aaa" }}>Elder not found</p>
    </div>
  );

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
              <Users size={16} color="#888" />
              <span style={styles.navText}>Elders</span>
            </div>
          </Link>
          <Link href="/add-elder" style={{ textDecoration: "none" }}>
            <div style={styles.navItem}>
              <Phone size={16} color="#888" />
              <span style={styles.navText}>Add Elder</span>
            </div>
          </Link>
        </nav>
        <div style={styles.sidebarFooter}>
          <div style={styles.statusDot}></div>
          <span style={styles.statusText}>System Online</span>
        </div>
      </div>

      {/* Main */}
      <div style={styles.main}>

        {/* Header */}
        <div style={styles.topBar}>
          <div style={styles.backRow}>
            <Link href="/" style={{ textDecoration: "none" }}>
              <button style={styles.backBtn}>
                <ArrowLeft size={16} color="#111" />
                Back
              </button>
            </Link>
            <div style={styles.divider}></div>
            <div>
              <h1 style={styles.pageTitle}>{elder.name}</h1>
              <p style={styles.pageSubtitle}>Elder Profile & Call History</p>
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div style={styles.grid}>

          {/* Left Column */}
          <div style={styles.leftCol}>

            {/* Profile Card */}
            <div style={styles.card}>
              <div style={styles.profileHeader}>
                <div style={styles.avatar}>{elder.name.charAt(0)}</div>
                <div>
                  <h2 style={styles.elderName}>{elder.name}</h2>
                  <p style={styles.elderPhone}>{elder.phone}</p>
                </div>
              </div>
              <div style={styles.dividerLine}></div>
              <div style={styles.infoGrid}>
                <div style={styles.infoRow}>
                  <Clock size={14} color="#999" />
                  <span style={styles.infoLabel}>Call Time</span>
                  <span style={styles.infoValue}>{elder.call_time}</span>
                </div>
                <div style={styles.infoRow}>
                  <Globe size={14} color="#999" />
                  <span style={styles.infoLabel}>Language</span>
                  <span style={styles.infoValue}>
                    {elder.language.charAt(0).toUpperCase() + elder.language.slice(1)}
                  </span>
                </div>
                <div style={styles.infoRow}>
                  <Users size={14} color="#999" />
                  <span style={styles.infoLabel}>Contacts</span>
                  <span style={styles.infoValue}>
                    {elder.family_contacts?.length || 0} family members
                  </span>
                </div>
              </div>
            </div>

            {/* Schedule Card */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <Calendar size={16} color="#111" />
                <h3 style={styles.cardTitle}>Call Schedule</h3>
              </div>
              <p style={styles.cardSubtitle}>
                Currently calling daily at <strong>{elder.call_time}</strong>
              </p>
              <div style={styles.scheduleRow}>
                <input
                  type="time"
                  value={newTime}
                  onChange={e => setNewTime(e.target.value)}
                  style={styles.timeInput}
                />
                <button onClick={updateCallTime} style={styles.updateBtn}>
                  Update
                </button>
              </div>
            </div>

            {/* Family Contacts Card */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <Users size={16} color="#111" />
                <h3 style={styles.cardTitle}>Family Contacts</h3>
              </div>
              {elder.family_contacts?.length > 0 ? (
                <div style={styles.contactList}>
                  {elder.family_contacts
                    .sort((a, b) => a.priority - b.priority)
                    .map((contact, i) => (
                      <div key={i} style={styles.contactRow}>
                        <div style={styles.contactAvatar}>
                          {contact.name.charAt(0)}
                        </div>
                        <div style={{ flex: 1 }}>
                          <p style={styles.contactName}>{contact.name}</p>
                          <p style={styles.contactPhone}>{contact.phone}</p>
                        </div>
                        <span style={styles.priorityBadge}>
                          P{contact.priority}
                        </span>
                      </div>
                    ))}
                </div>
              ) : (
                <p style={styles.emptyText}>No contacts added</p>
              )}
            </div>
          </div>

          {/* Right Column */}
          <div style={styles.rightCol}>

            {/* Memory Card */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <Brain size={16} color="#111" />
                <h3 style={styles.cardTitle}>AI Memory</h3>
              </div>
              <p style={styles.cardSubtitle}>
                What the AI knows from previous calls
              </p>
              <div style={styles.memoryBox}>
                <p style={styles.memoryText}>
                  {elder.memory_summary || "No previous calls yet. Memory will be built after the first conversation."}
                </p>
              </div>
            </div>

            {/* Alerts Card */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <Bell size={16} color="#111" />
                <h3 style={styles.cardTitle}>Recent Alerts</h3>
                <span style={styles.alertCount}>{alerts.length}</span>
              </div>

              {alerts.length === 0 ? (
                <div style={styles.noAlerts}>
                  <p style={styles.noAlertsText}>No alerts — all good ✓</p>
                </div>
              ) : (
                <div style={styles.alertList}>
                  {alerts.slice(0, 10).map((alert) => (
                    <div key={alert.id} style={{
                      ...styles.alertItem,
                      border: getAlertBorder(alert.alert_level)
                    }}>
                      <div style={styles.alertTop}>
                        <span style={styles.alertIcon}>
                          {getAlertIcon(alert.alert_level)}
                        </span>
                        <span style={styles.alertType}>
                          {alert.alert_type.replace(/_/g, " ").toUpperCase()}
                        </span>
                        <span style={styles.alertLevel}>
                          {alert.alert_level}
                        </span>
                      </div>
                      <p style={styles.alertReason}>{alert.alert_reason}</p>
                      <p style={styles.alertTime}>
                        {new Date(alert.sent_at).toLocaleString("en-IN")}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
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
  loading: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#f5f5f5",
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
  sidebarFooter: {
    padding: "16px 20px",
    borderTop: "1px solid #222",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  statusDot: { width: "7px", height: "7px", background: "#fff", borderRadius: "50%" },
  statusText: { fontSize: "12px", color: "#666" },
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
  grid: { display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: "20px" },
  leftCol: { display: "flex", flexDirection: "column", gap: "16px" },
  rightCol: { display: "flex", flexDirection: "column", gap: "16px" },
  card: {
    background: "white",
    borderRadius: "14px",
    padding: "22px",
    border: "1px solid #e8e8e8",
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "12px",
  },
  cardTitle: {
    margin: 0,
    fontSize: "14px",
    fontWeight: "700",
    color: "#111",
    flex: 1,
  },
  cardSubtitle: { margin: "0 0 14px", fontSize: "12px", color: "#aaa" },
  profileHeader: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    marginBottom: "16px",
  },
  avatar: {
    width: "48px",
    height: "48px",
    background: "#111",
    borderRadius: "12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "white",
    fontSize: "20px",
    fontWeight: "800",
  },
  elderName: { margin: 0, fontSize: "17px", fontWeight: "700", color: "#111" },
  elderPhone: { margin: "3px 0 0", fontSize: "12px", color: "#aaa" },
  dividerLine: { height: "1px", background: "#f0f0f0", margin: "0 0 14px" },
  infoGrid: { display: "flex", flexDirection: "column", gap: "10px" },
  infoRow: { display: "flex", alignItems: "center", gap: "8px" },
  infoLabel: { fontSize: "13px", color: "#aaa", flex: 1 },
  infoValue: { fontSize: "13px", fontWeight: "600", color: "#111" },
  scheduleRow: { display: "flex", gap: "8px" },
  timeInput: {
    flex: 1,
    border: "1px solid #e8e8e8",
    borderRadius: "8px",
    padding: "8px 12px",
    fontSize: "14px",
    color: "#111",
    outline: "none",
  },
  updateBtn: {
    background: "#111",
    color: "white",
    border: "none",
    padding: "8px 16px",
    borderRadius: "8px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
  contactList: { display: "flex", flexDirection: "column", gap: "10px" },
  contactRow: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px",
    background: "#fafafa",
    borderRadius: "8px",
    border: "1px solid #f0f0f0",
  },
  contactAvatar: {
    width: "32px",
    height: "32px",
    background: "#111",
    borderRadius: "8px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "white",
    fontSize: "13px",
    fontWeight: "700",
  },
  contactName: { margin: 0, fontSize: "13px", fontWeight: "600", color: "#111" },
  contactPhone: { margin: "2px 0 0", fontSize: "11px", color: "#aaa" },
  priorityBadge: {
    background: "#f0f0f0",
    color: "#555",
    fontSize: "11px",
    fontWeight: "700",
    padding: "3px 8px",
    borderRadius: "6px",
  },
  emptyText: { fontSize: "13px", color: "#aaa", margin: 0 },
  memoryBox: {
    background: "#fafafa",
    borderRadius: "10px",
    padding: "14px 16px",
    borderLeft: "2px solid #111",
  },
  memoryText: {
    margin: 0,
    fontSize: "13px",
    color: "#555",
    lineHeight: "1.7",
  },
  alertCount: {
    background: "#111",
    color: "white",
    fontSize: "11px",
    fontWeight: "700",
    padding: "2px 8px",
    borderRadius: "10px",
  },
  noAlerts: {
    padding: "20px",
    textAlign: "center",
    background: "#fafafa",
    borderRadius: "8px",
  },
  noAlertsText: { margin: 0, fontSize: "13px", color: "#aaa" },
  alertList: { display: "flex", flexDirection: "column", gap: "10px" },
  alertItem: {
    borderRadius: "10px",
    padding: "12px 14px",
    background: "#fafafa",
  },
  alertTop: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    marginBottom: "6px",
  },
  alertIcon: { fontSize: "14px" },
  alertType: {
    fontSize: "10px",
    fontWeight: "700",
    color: "#999",
    letterSpacing: "0.06em",
    flex: 1,
  },
  alertLevel: {
    fontSize: "10px",
    fontWeight: "700",
    color: "#111",
    background: "#f0f0f0",
    padding: "2px 8px",
    borderRadius: "4px",
  },
  alertReason: { margin: "0 0 4px", fontSize: "12px", color: "#444", lineHeight: "1.5" },
  alertTime: { margin: 0, fontSize: "11px", color: "#bbb" },
};