import "./App.css";

type Activity = {
  id: string;
  subject: string;
  status: "Verified" | "Mismatch" | "Needs Review";
  confidence: number;
};

const recentActivity: Activity[] = [
  {
    id: "email_004",
    subject: "REQUEST BL DRAFT - PO 26067",
    status: "Mismatch",
    confidence: 96,
  },
  {
    id: "email_012",
    subject: "Draft BL verification request",
    status: "Verified",
    confidence: 99,
  },
  {
    id: "email_021",
    subject: "Shipping document review",
    status: "Needs Review",
    confidence: 58,
  },
  {
    id: "email_028",
    subject: "BL confirmation required",
    status: "Verified",
    confidence: 97,
  },
];

function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">C</div>

          <div>
            <h1>CargoSense</h1>
            <span>AI Document Verification</span>
          </div>
        </div>

        <nav>
          <button className="nav-item active">Dashboard</button>
          <button className="nav-item">Inbox</button>
          <button className="nav-item">Human Review</button>
          <button className="nav-item">Analytics</button>
        </nav>

        <div className="sidebar-footer">
          <span className="status-dot"></span>
          System Online
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Shipping Operations</p>
            <h2>Document Verification Dashboard</h2>
          </div>

          <div className="ai-badge">
            <span className="status-dot"></span>
            AI Engine Active
          </div>
        </header>

        <section className="stats-grid">
          <StatCard
            title="Emails Processed"
            value="128"
            description="+18 today"
          />

          <StatCard
            title="Discrepancies"
            value="17"
            description="13.3% of checks"
          />

          <StatCard
            title="Human Review"
            value="4"
            description="Requires attention"
          />

          <StatCard
            title="Automation Rate"
            value="94.8%"
            description="Successfully automated"
          />
        </section>

        <section className="content-grid">
          <div className="panel activity-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Live Processing</p>
                <h3>Recent Activity</h3>
              </div>

              <button className="secondary-button">View Inbox</button>
            </div>

            <div className="activity-list">
              {recentActivity.map((item) => (
                <div className="activity-row" key={item.id}>
                  <div className="email-info">
                    <div className="email-icon">✉</div>

                    <div>
                      <strong>{item.subject}</strong>
                      <span>{item.id}</span>
                    </div>
                  </div>

                  <div className="activity-result">
                    <StatusBadge status={item.status} />
                    <span className="confidence">
                      {item.confidence}% confidence
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel performance-panel">
            <div>
              <p className="eyebrow">AI Performance</p>
              <h3>Processing Overview</h3>
            </div>

            <div className="performance-stat">
              <div>
                <span>Average Confidence</span>
                <strong>96.2%</strong>
              </div>

              <div className="progress">
                <div className="progress-bar confidence-bar"></div>
              </div>
            </div>

            <div className="performance-stat">
              <div>
                <span>Automatic Processing</span>
                <strong>94.8%</strong>
              </div>

              <div className="progress">
                <div className="progress-bar automation-bar"></div>
              </div>
            </div>

            <div className="mini-stats">
              <div>
                <strong>7</strong>
                <span>Fields Checked</span>
              </div>

              <div>
                <strong>5</strong>
                <span>Email Categories</span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function StatCard({
  title,
  value,
  description,
}: {
  title: string;
  value: string;
  description: string;
}) {
  return (
    <div className="stat-card">
      <span>{title}</span>
      <strong>{value}</strong>
      <p>{description}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: Activity["status"] }) {
  const className = status.toLowerCase().replace(" ", "-");

  return <span className={`status-badge ${className}`}>{status}</span>;
}

export default App;