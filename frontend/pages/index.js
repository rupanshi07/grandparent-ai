import { useState, useEffect } from "react";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/router";
import { Phone, Users, Activity, ChevronRight,
         Clock, Globe, AlertCircle, PhoneCall } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const router = useRouter();
  const [elders, setElders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [calling, setCalling] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }
    const storedUser = localStorage.getItem("user");
    if (storedUser) setUser(JSON.parse(storedUser));

    fetchElders();
    const interval = setInterval(fetchElders, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchElders = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }
    try {
      const res = await axios.get(`${API}/elders`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setElders(res.data.elders);
    } catch (e) {
      if (e.response?.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        router.push("/login");
      }
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    router.push("/login");
  };
  const triggerCall = async (elderId, elderName) => {
    setCalling(elderId);
    try {
      await axios.post(`${API}/test/call`);
    } catch (e) {
      console.error(e);
    } finally {
      setTimeout(() => setCalling(null), 3000);
    }
  };

  if (loading) return (
    <div style={styles.loadingContainer}>
      <div style={styles.loadingDot}></div>
      <p style={styles.loadingText}>Loading dashboard...</p>
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
          <div style={styles.navItemActive}>
            <Users size={16} color="white" />
            <span style={styles.navTextActive}>Elders</span>
          </div>
          <Link href="/add-elder" style={{ textDecoration: "none" }}>
            <div style={styles.navItem}>
              <Phone size={16} color="#888" />
              <span style={styles.navText}>Add Elder</span>
            </div>
          </Link>
        </nav>

        <div style={styles.sidebarFooter}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
              <div style={styles.statusDot}></div>
              <span style={styles.statusText}>System Online</span>
            </div>
            {user && (
              <p style={{ fontSize: "11px", color: "#888", margin: "0 0 8px" }}>
                {user.email}
              </p>
            )}
            <button onClick={handleLogout} style={styles.logoutBtn}>
              Log Out
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={styles.main}>

        {/* Top Bar */}
        <div style={styles.topBar}>
          <div>
            <h1 style={styles.pageTitle}>Dashboard</h1>
            <p style={styles.pageSubtitle}>
              Monitor and manage your elderly loved ones
            </p>
          </div>
          <Link href="/add-elder" style={{ textDecoration: "none" }}>
            <button style={styles.addButton}>+ Add Elder</button>
          </Link>
        </div>

        {/* Stats Cards */}
        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <div style={styles.statIcon}>
              <Users size={20} color="#111" />
            </div>
            <div>
              <p style={styles.statLabel}>Total Elders</p>
              <p style={styles.statValue}>{elders.length}</p>
            </div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statIcon}>
              <Activity size={20} color="#111" />
            </div>
            <div>
              <p style={styles.statLabel}>Active Today</p>
              <p style={styles.statValue}>{elders.length}</p>
            </div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statIcon}>
              <PhoneCall size={20} color="#111" />
            </div>
            <div>
              <p style={styles.statLabel}>Calls Today</p>
              <p style={styles.statValue}>{elders.length}</p>
            </div>
          </div>
        </div>

        {/* Elders Section */}
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Registered Elders</h2>

          {elders.length === 0 ? (
            <div style={styles.emptyState}>
              <Users size={48} color="#ddd" />
              <p style={styles.emptyText}>No elders registered yet</p>
              <Link href="/add-elder">
                <button style={styles.addButton}>Add First Elder</button>
              </Link>
            </div>
          ) : (
            <div style={styles.elderGrid}>
              {elders.map((elder) => (
                <div key={elder.id} style={styles.elderCard}>

                  {/* Card Header */}
                  <div style={styles.cardHeader}>
                    <div style={styles.avatar}>
                      {elder.name.charAt(0)}
                    </div>
                    <div style={styles.elderInfo}>
                      <h3 style={styles.elderName}>{elder.name}</h3>
                      <p style={styles.elderPhone}>{elder.phone}</p>
                    </div>
                    <div style={styles.statusBadge}>
                      <div style={styles.activeDot}></div>
                      <span style={styles.activeText}>Active</span>
                    </div>
                  </div>

                  {/* Card Details */}
                  <div style={styles.cardDetails}>
                    <div style={styles.detailRow}>
                      <Clock size={13} color="#999" />
                      <span style={styles.detailText}>
                        Daily call at {elder.call_time}
                      </span>
                    </div>
                    <div style={styles.detailRow}>
                      <Globe size={13} color="#999" />
                      <span style={styles.detailText}>
                        {elder.language.charAt(0).toUpperCase() + elder.language.slice(1)}
                      </span>
                    </div>
                    {elder.family_contacts?.length > 0 && (
                      <div style={styles.detailRow}>
                        <Users size={13} color="#999" />
                        <span style={styles.detailText}>
                          {elder.family_contacts.length} family contact{elder.family_contacts.length > 1 ? "s" : ""}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Memory Preview */}
                  {elder.memory_summary && (
                    <div style={styles.memoryBox}>
                      <p style={styles.memoryLabel}>LAST KNOWN STATUS</p>
                      <p style={styles.memoryText}>
                        {elder.memory_summary.substring(0, 120)}...
                      </p>
                    </div>
                  )}

                  {/* Card Actions */}
                  <div style={styles.cardActions}>
                    <button
                      onClick={() => triggerCall(elder.id, elder.name)}
                      style={{
                        ...styles.callButton,
                        background: calling === elder.id ? "#333" : "#111",
                      }}>
                      <Phone size={13} color="white" />
                      {calling === elder.id ? "Calling..." : "Call Now"}
                    </button>
                    <Link href={`/elder/${elder.id}`}
                      style={{ textDecoration: "none", flex: 1 }}>
                      <button style={styles.detailButton}>
                        View Details
                        <ChevronRight size={13} color="#111" />
                      </button>
                    </Link>
                  </div>

                </div>
              ))}
            </div>
          )}
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
  logoTitle: {
    margin: 0,
    fontWeight: "700",
    fontSize: "14px",
    color: "white",
  },
  logoSub: {
    margin: 0,
    fontSize: "11px",
    color: "#555",
  },
  nav: { padding: "0 12px", flex: 1 },
  navItemActive: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px 12px",
    borderRadius: "8px",
    cursor: "pointer",
    marginBottom: "4px",
    background: "#fff",
  },
  navTextActive: {
    fontSize: "13px",
    color: "#111",
    fontWeight: "700",
  },
  navItem: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px 12px",
    borderRadius: "8px",
    cursor: "pointer",
    marginBottom: "4px",
  },
  navText: {
    fontSize: "13px",
    color: "#888",
    textDecoration: "none",
  },
  sidebarFooter: {
    padding: "16px 20px",
    borderTop: "1px solid #222",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  statusDot: {
    width: "7px",
    height: "7px",
    background: "#fff",
    borderRadius: "50%",
  },
  statusText: { fontSize: "12px", color: "#666" },
  logoutBtn: {
    width: "100%",
    background: "transparent",
    border: "1px solid #333",
    color: "#ccc",
    padding: "7px",
    borderRadius: "6px",
    fontSize: "12px",
    cursor: "pointer",
  },
  main: {
    marginLeft: "230px",
    flex: 1,
    padding: "40px 44px",
  },
  topBar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "32px",
    paddingBottom: "24px",
    borderBottom: "1px solid #e0e0e0",
  },
  pageTitle: {
    margin: 0,
    fontSize: "28px",
    fontWeight: "800",
    color: "#111",
    letterSpacing: "-0.6px",
  },
  pageSubtitle: {
    margin: "5px 0 0",
    fontSize: "13px",
    color: "#aaa",
  },
  addButton: {
    background: "#111",
    color: "white",
    border: "none",
    padding: "10px 22px",
    borderRadius: "8px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "16px",
    marginBottom: "36px",
  },
  statCard: {
    background: "white",
    borderRadius: "12px",
    padding: "22px",
    display: "flex",
    alignItems: "center",
    gap: "16px",
    border: "1px solid #e8e8e8",
  },
  statIcon: {
    width: "42px",
    height: "42px",
    borderRadius: "10px",
    background: "#f3f3f3",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  statLabel: {
    margin: 0,
    fontSize: "12px",
    color: "#aaa",
    fontWeight: "500",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  statValue: {
    margin: "4px 0 0",
    fontSize: "28px",
    fontWeight: "800",
    color: "#111",
    letterSpacing: "-0.5px",
  },
  section: { marginBottom: "28px" },
  sectionTitle: {
    fontSize: "17px",
    fontWeight: "700",
    color: "#111",
    marginBottom: "16px",
    letterSpacing: "-0.3px",
  },
  elderGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
    gap: "16px",
  },
  elderCard: {
    background: "white",
    borderRadius: "14px",
    padding: "22px",
    border: "1px solid #e8e8e8",
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    marginBottom: "16px",
  },
  avatar: {
    width: "46px",
    height: "46px",
    background: "#111",
    borderRadius: "12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "white",
    fontSize: "18px",
    fontWeight: "800",
  },
  elderInfo: { flex: 1 },
  elderName: {
    margin: 0,
    fontSize: "16px",
    fontWeight: "700",
    color: "#111",
    letterSpacing: "-0.2px",
  },
  elderPhone: {
    margin: "3px 0 0",
    fontSize: "12px",
    color: "#aaa",
  },
  statusBadge: {
    display: "flex",
    alignItems: "center",
    gap: "5px",
    background: "#f5f5f5",
    padding: "4px 10px",
    borderRadius: "20px",
    border: "1px solid #e8e8e8",
  },
  activeDot: {
    width: "6px",
    height: "6px",
    background: "#111",
    borderRadius: "50%",
  },
  activeText: {
    fontSize: "11px",
    color: "#111",
    fontWeight: "700",
    letterSpacing: "0.02em",
  },
  cardDetails: {
    display: "flex",
    flexDirection: "column",
    gap: "7px",
    marginBottom: "16px",
    paddingBottom: "16px",
    borderBottom: "1px solid #f0f0f0",
  },
  detailRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  detailText: {
    fontSize: "13px",
    color: "#777",
  },
  memoryBox: {
    background: "#fafafa",
    borderRadius: "8px",
    padding: "12px 14px",
    marginBottom: "16px",
    borderLeft: "2px solid #111",
  },
  memoryLabel: {
    margin: "0 0 5px",
    fontSize: "9px",
    fontWeight: "700",
    color: "#bbb",
    letterSpacing: "0.1em",
  },
  memoryText: {
    margin: 0,
    fontSize: "12px",
    color: "#666",
    lineHeight: "1.6",
  },
  cardActions: {
    display: "flex",
    gap: "8px",
  },
  callButton: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "9px 16px",
    borderRadius: "8px",
    border: "none",
    color: "white",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
  detailButton: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "4px",
    padding: "9px 16px",
    borderRadius: "8px",
    border: "1px solid #e8e8e8",
    background: "white",
    color: "#111",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
    width: "100%",
  },
  emptyState: {
    background: "white",
    borderRadius: "16px",
    padding: "60px",
    textAlign: "center",
    border: "1px solid #e8e8e8",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "16px",
  },
  emptyText: {
    fontSize: "15px",
    color: "#aaa",
    margin: 0,
  },
  loadingContainer: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: "12px",
    background: "#f5f5f5",
  },
  loadingDot: {
    width: "36px",
    height: "36px",
    background: "#111",
    borderRadius: "50%",
  },
  loadingText: {
    color: "#aaa",
    fontSize: "13px",
  },
};