import { useMemo, useState } from "react";
import "./App.css";

type Page =
  | "dashboard"
  | "inbox"
  | "comparison"
  | "review";

type Status =
  | "Verified"
  | "Mismatch"
  | "Needs Review"
  | "Classified";

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

type ComparisonField = {
  label: string;
  siValue: string;
  blValue: string;
  match: boolean;
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

const comparisonFields: ComparisonField[] = [
  {
    label: "Shipper",
    siValue: "APRIL FAR EAST (M) SDN BHD",
    blValue: "APRIL FAR EAST (M) SDN BHD",
    match: true,
  },
  {
    label: "Consignee",
    siValue: "EAST BRIGHT FZ-LLC",
    blValue: "UAB NOVAKOPA",
    match: false,
  },
  {
    label: "Notify Party",
    siValue: "EAST BRIGHT FZ-LLC",
    blValue: "UAB NOVAKOPA",
    match: false,
  },
  {
    label: "Port of Loading",
    siValue: "NANTONG, CHINA (CNNTG)",
    blValue: "NANTONG, CHINA (CNNTG)",
    match: true,
  },
  {
    label: "Port of Discharge",
    siValue: "KARACHI, PAKISTAN (PKKHI)",
    blValue: "KARACHI, PAKISTAN (PKKHI)",
    match: true,
  },
  {
    label: "Container Count",
    siValue: "6",
    blValue: "6",
    match: true,
  },
  {
    label: "Gross Weight",
    siValue: "131,058 kg",
    blValue: "131,058 kg",
    match: true,
  },
];

function App() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="app">
      <Sidebar page={page} setPage={setPage} />

      <main className="main-content">
        {page === "dashboard" && (
          <Dashboard onViewInbox={() => setPage("inbox")} />
        )}

        {page === "inbox" && (
          <Inbox
            onOpenComparison={() => setPage("comparison")}
          />
        )}

        {page === "comparison" && (
          <ComparisonPage
            onBack={() => setPage("inbox")}
          />
        )}

        {page === "review" && <HumanReview />}
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
          className={`nav-item ${
            page === "dashboard" ? "active" : ""
          }`}
          onClick={() => setPage("dashboard")}
        >
          Dashboard
        </button>

        <button
          className={`nav-item ${
            page === "inbox" ||
            page === "comparison"
              ? "active"
              : ""
          }`}
          onClick={() => setPage("inbox")}
        >
          Inbox
        </button>

        <button
          className={`nav-item ${
            page === "review" ? "active" : ""
          }`}
          onClick={() => setPage("review")}
        >
          Human Review
        </button>

        <button className="nav-item">
          Analytics
        </button>
      </nav>

      <div className="sidebar-footer">
        <span className="status-dot"></span>
        System Online
      </div>
    </aside>
  );
}

function Dashboard({
  onViewInbox,
}: {
  onViewInbox: () => void;
}) {
  const recentActivity = emails.slice(0, 4);

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">
            Shipping Operations
          </p>
          <h2>
            Document Verification Dashboard
          </h2>
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
              <p className="eyebrow">
                Live Processing
              </p>
              <h3>Recent Activity</h3>
            </div>

            <button
              className="secondary-button"
              onClick={onViewInbox}
            >
              View Inbox
            </button>
          </div>

          <div className="activity-list">
            {recentActivity.map((item) => (
              <div
                className="activity-row"
                key={item.id}
              >
                <div className="email-info">
                  <div className="email-icon">
                    ✉
                  </div>

                  <div>
                    <strong>
                      {item.subject}
                    </strong>
                    <span>{item.id}</span>
                  </div>
                </div>

                <div className="activity-result">
                  <StatusBadge
                    status={item.status}
                  />

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
            <p className="eyebrow">
              AI Performance
            </p>
            <h3>Processing Overview</h3>
          </div>

          <div className="performance-stat">
            <div>
              <span>
                Average Confidence
              </span>
              <strong>96.2%</strong>
            </div>

            <div className="progress">
              <div className="progress-bar confidence-bar"></div>
            </div>
          </div>

          <div className="performance-stat">
            <div>
              <span>
                Automatic Processing
              </span>
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

function Inbox({
  onOpenComparison,
}: {
  onOpenComparison: () => void;
}) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] =
    useState<"All" | Category>("All");

  const filteredEmails = useMemo(() => {
    return emails.filter((email) => {
      const matchesSearch =
        email.subject
          .toLowerCase()
          .includes(search.toLowerCase()) ||
        email.sender
          .toLowerCase()
          .includes(search.toLowerCase()) ||
        email.id
          .toLowerCase()
          .includes(search.toLowerCase());

      const matchesFilter =
        filter === "All" ||
        email.category === filter;

      return matchesSearch && matchesFilter;
    });
  }, [search, filter]);

  const filters: Array<
    "All" | Category
  > = [
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
          <p className="eyebrow">
            AI Mail Processing
          </p>
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
              onChange={(event) =>
                setSearch(event.target.value)
              }
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
                filter === item
                  ? "active-filter"
                  : ""
              }`}
              onClick={() =>
                setFilter(item)
              }
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
            <button
              className="inbox-row"
              key={email.id}
              onClick={() => {
                if (
                  email.id === "email_004"
                ) {
                  onOpenComparison();
                }
              }}
            >
              <div className="inbox-email">
                <div className="email-icon">
                  ✉
                </div>

                <div>
                  <strong>
                    {email.subject}
                  </strong>

                  <span>
                    {email.sender} ·{" "}
                    {email.id}
                  </span>

                  {email.attachments >
                    0 && (
                    <small>
                      {email.attachments}{" "}
                      attachment
                      {email.attachments !==
                      1
                        ? "s"
                        : ""}
                    </small>
                  )}
                </div>
              </div>

              <CategoryBadge
                category={email.category}
              />

              <StatusBadge
                status={email.status}
              />

              <div className="confidence-cell">
                <strong>
                  {email.confidence}%
                </strong>

                <div className="confidence-track">
                  <div
                    className="confidence-fill"
                    style={{
                      width: `${email.confidence}%`,
                    }}
                  ></div>
                </div>
              </div>

              <span className="received-time">
                {email.receivedAt}
              </span>
            </button>
          ))}

          {filteredEmails.length === 0 && (
            <div className="empty-state">
              <strong>
                No emails found
              </strong>
              <span>
                Try a different search or
                filter.
              </span>
            </div>
          )}
        </div>
      </section>
    </>
  );
}

function ComparisonPage({
  onBack,
}: {
  onBack: () => void;
}) {
  const mismatchCount =
    comparisonFields.filter(
      (field) => !field.match,
    ).length;

  return (
    <>
      <button
        className="back-button"
        onClick={onBack}
      >
        ← Back to Inbox
      </button>

      <header className="comparison-header">
        <div>
          <p className="eyebrow">
            Document Verification
          </p>

          <h2>
            REQUEST BL DRAFT - PO 26067
          </h2>

          <p className="comparison-subtitle">
            email_004 ·
            operations@shipping.com
          </p>
        </div>

        <div className="comparison-header-right">
          <StatusBadge status="Mismatch" />

          <span className="comparison-confidence">
            96% confidence
          </span>
        </div>
      </header>

      <section className="comparison-summary">
        <div className="summary-icon">
          !
        </div>

        <div>
          <strong>
            {mismatchCount} discrepancies
            detected
          </strong>

          <p>
            The draft Bill of Lading does
            not fully match the Shipping
            Instruction.
          </p>
        </div>
      </section>

      <section className="panel comparison-panel">
        <div className="comparison-title-row">
          <div>
            <p className="eyebrow">
              Field Verification
            </p>
            <h3>
              SI ↔ BL Comparison
            </h3>
          </div>

          <span className="field-count">
            7 fields checked
          </span>
        </div>

        <div className="comparison-table">
          <div className="comparison-table-header">
            <span>Field</span>
            <span>
              Shipping Instruction
            </span>
            <span>
              Bill of Lading
            </span>
            <span>Result</span>
          </div>

          {comparisonFields.map(
            (field) => (
              <div
                className={`comparison-row ${
                  !field.match
                    ? "comparison-mismatch"
                    : ""
                }`}
                key={field.label}
              >
                <strong>
                  {field.label}
                </strong>

                <span>
                  {field.siValue}
                </span>

                <span>
                  {field.blValue}
                </span>

                <span
                  className={
                    field.match
                      ? "field-result match"
                      : "field-result mismatch"
                  }
                >
                  {field.match
                    ? "✓ Match"
                    : "⚠ Mismatch"}
                </span>
              </div>
            ),
          )}
        </div>
      </section>

      <section className="comparison-bottom-grid">
        <div className="panel discrepancy-panel">
          <p className="eyebrow">
            Attention Required
          </p>

          <h3>
            Detected Discrepancies
          </h3>

          <div className="discrepancy-item">
            <strong>Consignee</strong>

            <div className="difference-values">
              <div>
                <span>
                  Shipping Instruction
                </span>
                <p>
                  EAST BRIGHT FZ-LLC
                </p>
              </div>

              <div>
                <span>
                  Bill of Lading
                </span>
                <p>UAB NOVAKOPA</p>
              </div>
            </div>
          </div>

          <div className="discrepancy-item">
            <strong>
              Notify Party
            </strong>

            <div className="difference-values">
              <div>
                <span>
                  Shipping Instruction
                </span>
                <p>
                  EAST BRIGHT FZ-LLC
                </p>
              </div>

              <div>
                <span>
                  Bill of Lading
                </span>
                <p>UAB NOVAKOPA</p>
              </div>
            </div>
          </div>
        </div>

        <div className="panel processing-panel">
          <p className="eyebrow">
            AI Processing
          </p>

          <h3>
            Verification Details
          </h3>

          <div className="processing-line">
            <span>
              Email classification
            </span>
            <strong>
              BL Comparison
            </strong>
          </div>

          <div className="processing-line">
            <span>
              Documents detected
            </span>
            <strong>2 / 2</strong>
          </div>

          <div className="processing-line">
            <span>
              Fields extracted
            </span>
            <strong>14 / 14</strong>
          </div>

          <div className="processing-line">
            <span>
              Fields compared
            </span>
            <strong>7 / 7</strong>
          </div>

          <div className="processing-line">
            <span>
              Human review
            </span>
            <strong>
              Not required
            </strong>
          </div>
        </div>
      </section>
    </>
  );
}

function HumanReview() {
  const [
    correctedValue,
    setCorrectedValue,
  ] = useState("");

  const [resolved, setResolved] =
    useState(false);

  if (resolved) {
    return (
      <>
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Human-in-the-Loop
            </p>
            <h2>Review Queue</h2>
          </div>

          <div className="ai-badge">
            <span className="status-dot"></span>
            Review saved
          </div>
        </header>

        <section className="panel review-success">
          <div className="success-check">
            ✓
          </div>

          <h3>Case resolved</h3>

          <p>
            The corrected value has been
            confirmed and the verification
            result can now continue
            processing.
          </p>

          <button
            className="primary-button"
            onClick={() => {
              setResolved(false);
              setCorrectedValue("");
            }}
          >
            View Review Queue
          </button>
        </section>
      </>
    );
  }

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">
            Human-in-the-Loop
          </p>

          <h2>Review Queue</h2>
        </div>

        <div className="review-count">
          1 case requires attention
        </div>
      </header>

      <section className="review-layout">
        <div className="panel review-case">
          <div className="review-case-header">
            <div>
              <span className="review-priority">
                Needs Review
              </span>

              <h3>
                Shipping document review
              </h3>

              <p>
                email_021 ·
                docs@freight.com
              </p>
            </div>

            <div className="confidence-warning">
              58%
              <span>confidence</span>
            </div>
          </div>

          <div className="review-reason">
            <strong>
              Why was this escalated?
            </strong>

            <p>
              The AI could not confidently
              determine the consignee value
              from the Shipping Instruction.
              Human confirmation is required
              before the comparison
              continues.
            </p>
          </div>

          <div className="source-evidence">
            <p className="eyebrow">
              Source Evidence
            </p>

            <h3>
              Shipping Instruction
            </h3>

            <div className="document-preview">
              <div className="document-line">
                <span>SHIPPER</span>

                <strong>
                  PACIFIC GLOBAL TRADING
                  SDN BHD
                </strong>
              </div>

              <div className="document-line uncertain-line">
                <span>
                  CONSIGNEE
                </span>

                <strong>
                  BLUE OC... LOGISTICS SDN
                  BHD
                </strong>

                <span className="uncertain-badge">
                  Low confidence
                </span>
              </div>

              <div className="document-line">
                <span>
                  PORT OF LOADING
                </span>

                <strong>
                  PORT KLANG, MALAYSIA
                </strong>
              </div>
            </div>
          </div>
        </div>

        <div className="panel review-action-panel">
          <p className="eyebrow">
            AI Extraction
          </p>

          <h3>
            Confirm extracted value
          </h3>

          <div className="ai-suggestion">
            <span>AI suggestion</span>

            <strong>
              BLUE OCEAN LOGISTICS SDN BHD
            </strong>

            <div className="suggestion-confidence">
              Confidence: 58%
            </div>
          </div>

          <label className="review-label">
            Correct consignee
          </label>

          <input
            className="review-input"
            placeholder="Enter the correct consignee..."
            value={correctedValue}
            onChange={(event) =>
              setCorrectedValue(
                event.target.value,
              )
            }
          />

          <button
            className="suggestion-button"
            onClick={() =>
              setCorrectedValue(
                "BLUE OCEAN LOGISTICS SDN BHD",
              )
            }
          >
            Use AI suggestion
          </button>

          <button
            className="primary-button resolve-button"
            disabled={
              !correctedValue.trim()
            }
            onClick={() =>
              setResolved(true)
            }
          >
            Confirm & Resolve
          </button>

          <p className="review-note">
            The confirmed value will be
            used to continue document
            verification.
          </p>
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

function StatusBadge({
  status,
}: {
  status: Status;
}) {
  const className = status
    .toLowerCase()
    .replaceAll(" ", "-");

  return (
    <span
      className={`status-badge ${className}`}
    >
      {status}
    </span>
  );
}

function CategoryBadge({
  category,
}: {
  category: Category;
}) {
  const className = category
    .toLowerCase()
    .replaceAll(" ", "-");

  return (
    <span
      className={`category-badge ${className}`}
    >
      {category}
    </span>
  );
}

export default App;