import { useMemo, useState } from "react";
import "./App.css";

type Page = "dashboard" | "inbox";

type Status = "Verified" | "Mismatch" | "Needs Review" | "Classified";

type Category =
  | "BL Comparison"
  | "SI Request"
  | "Invoice Query"
  | "General"
  | "Spam";

type EmailRecord = {
  id: string;
  subject: string;
  sender: string;
  category: Category;
  status: Status;
  confidence: number;
  attachments: number;
  receivedAt: string;
};

const emails: EmailRecord[] = [
  {
    id: "email_004",
    subject: "REQUEST BL DRAFT - PO 26067",
    sender: "operations@shipping.com",
    category: "BL Comparison",
    status: "Mismatch",
    confidence: 96,
    attachments: 2,
    receivedAt: "10:42 AM",
  },
  {
    id: "email_012",
    subject: "Draft BL verification request",
    sender: "export@logistics.com",
    category: "BL Comparison",
    status: "Verified",
    confidence: 99,
    attachments: 2,
    receivedAt: "10:18 AM",
  },
  {
    id: "email_021",
    subject: "Shipping document review",
    sender: "docs@freight.com",
    category: "BL Comparison",
    status: "Needs Review",
    confidence: 58,
    attachments: 2,
    receivedAt: "9:55 AM",
  },
  {
    id: "email_028",
    subject: "BL confirmation required",
    sender: "shipment@carrier.com",
    category: "BL Comparison",
    status: "Verified",
    confidence: 97,
    attachments: 2,
    receivedAt: "9:31 AM",
  },
  {
    id: "email_034",
    subject: "Please prepare new shipping instruction",
    sender: "customer@trading.com",
    category: "SI Request",
    status: "Classified",
    confidence: 95,
    attachments: 1,
    receivedAt: "9:14 AM",
  },
  {
    id: "email_041",
    subject: "Question regarding invoice INV-1048",
    sender: "finance@customer.com",
    category: "Invoice Query",
    status: "Classified",
    confidence: 93,
    attachments: 1,
    receivedAt: "8:48 AM",
  },
  {
    id: "email_052",
    subject: "Weekly operations update",
    sender: "manager@shipping.com",
    category: "General",
    status: "Classified",
    confidence: 98,
    attachments: 0,
    receivedAt: "8:20 AM",
  },
  {
    id: "email_061",
    subject: "YOU HAVE WON A FREE HOLIDAY!!!",
    sender: "promo@example.com",
    category: "Spam",
    status: "Classified",
    confidence: 99,
    attachments: 0,
    receivedAt: "7:52 AM",
  },
];

function App() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="app">
      <Sidebar page={page} setPage={setPage} />

      <main className="main-content">
        {page === "dashboard" ? (
          <Dashboard onViewInbox={() => setPage("inbox")} />
        ) : (
          <Inbox />
        )}
      </main>
    </div>
  );
}

function Sidebar({
  page,
  setPage,
}: {
  page: Page;
  setPage: (page: Page) => void;
}) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">C</div>

        <div>
          <h1>CargoSense</h1>
          <span>AI Document Verification</span>
        </div>
      </div>

      <nav>
        <button
          className={`nav-item ${page === "dashboard" ? "active" : ""}`}
          onClick={() => setPage("dashboard")}
        >
          Dashboard
        </button>

        <button
          className={`nav-item ${page === "inbox" ? "active" : ""}`}
          onClick={() => setPage("inbox")}
        >
          Inbox
        </button>

        <button className="nav-item">Human Review</button>
        <button className="nav-item">Analytics</button>
      </nav>

      <div className="sidebar-footer">
        <span className="status-dot"></span>
        System Online
      </div>
    </aside>
  );
}

function Dashboard({ onViewInbox }: { onViewInbox: () => void }) {
  const recentActivity = emails.slice(0, 4);

  return (
    <>
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

            <button className="secondary-button" onClick={onViewInbox}>
              View Inbox
            </button>
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
    </>
  );
}

function Inbox() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"All" | Category>("All");

  const filteredEmails = useMemo(() => {
    return emails.filter((email) => {
      const matchesSearch =
        email.subject.toLowerCase().includes(search.toLowerCase()) ||
        email.sender.toLowerCase().includes(search.toLowerCase()) ||
        email.id.toLowerCase().includes(search.toLowerCase());

      const matchesFilter =
        filter === "All" || email.category === filter;

      return matchesSearch && matchesFilter;
    });
  }, [search, filter]);

  const filters: Array<"All" | Category> = [
    "All",
    "BL Comparison",
    "SI Request",
    "Invoice Query",
    "General",
    "Spam",
  ];

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">AI Mail Processing</p>
          <h2>Inbox</h2>
        </div>

        <div className="ai-badge">
          <span className="status-dot"></span>
          {emails.length} emails loaded
        </div>
      </header>

      <section className="panel inbox-panel">
        <div className="inbox-toolbar">
          <div className="search-wrapper">
            <span>⌕</span>

            <input
              type="text"
              placeholder="Search emails, sender or ID..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>

          <span className="result-count">
            {filteredEmails.length} results
          </span>
        </div>

        <div className="filter-row">
          {filters.map((item) => (
            <button
              key={item}
              className={`filter-button ${
                filter === item ? "active-filter" : ""
              }`}
              onClick={() => setFilter(item)}
            >
              {item}
            </button>
          ))}
        </div>

        <div className="inbox-table">
          <div className="inbox-table-header">
            <span>Email</span>
            <span>Category</span>
            <span>Status</span>
            <span>Confidence</span>
            <span>Received</span>
          </div>

          {filteredEmails.map((email) => (
            <button className="inbox-row" key={email.id}>
              <div className="inbox-email">
                <div className="email-icon">✉</div>

                <div>
                  <strong>{email.subject}</strong>
                  <span>
                    {email.sender} · {email.id}
                  </span>

                  {email.attachments > 0 && (
                    <small>
                      {email.attachments} attachment
                      {email.attachments !== 1 ? "s" : ""}
                    </small>
                  )}
                </div>
              </div>

              <CategoryBadge category={email.category} />

              <StatusBadge status={email.status} />

              <div className="confidence-cell">
                <strong>{email.confidence}%</strong>

                <div className="confidence-track">
                  <div
                    className="confidence-fill"
                    style={{ width: `${email.confidence}%` }}
                  ></div>
                </div>
              </div>

              <span className="received-time">{email.receivedAt}</span>
            </button>
          ))}

          {filteredEmails.length === 0 && (
            <div className="empty-state">
              <strong>No emails found</strong>
              <span>Try a different search or filter.</span>
            </div>
          )}
        </div>
      </section>
    </>
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

function StatusBadge({ status }: { status: Status }) {
  const className = status.toLowerCase().replaceAll(" ", "-");

  return <span className={`status-badge ${className}`}>{status}</span>;
}

function CategoryBadge({ category }: { category: Category }) {
  const className = category.toLowerCase().replaceAll(" ", "-");

  return (
    <span className={`category-badge ${className}`}>
      {category}
    </span>
  );
}

export default App;