import type {
  BeforeAfter,
  CostEstimate,
  FixRoadmapItem,
  GTIN14Suggestion,
  GTINResult,
  HierarchyAnalysis,
  RetailerChecklist,
  Severity,
} from '../types'
import styles from './AnalysisSections.module.css'

function effortColor(v: string) {
  return v === 'Low' ? '#158f75' : v === 'Medium' ? '#ee8a2a' : '#cc100a'
}
function impactColor(v: string) {
  return v === 'High' ? '#cc100a' : v === 'Medium' ? '#ee8a2a' : '#158f75'
}

// ---------------------------------------------------------------------------
// Issues by Severity
// ---------------------------------------------------------------------------

export function IssuesBySeverity({ results }: { results: GTINResult[] }) {
  const critical = results.filter((r) => r.has_critical)
  const warning = results.filter((r) => r.has_warning && !r.has_critical)
  const info = results.filter(
    (r) => r.issues.length > 0 && !r.has_critical && !r.has_warning,
  )

  function renderGroup(
    items: GTINResult[],
    severity: Severity,
    label: string,
    badgeClass: string,
    desc: string,
  ) {
    if (!items.length) return null
    return (
      <>
        <p>
          <span className={`badge ${badgeClass}`}>{label}</span> &mdash; {desc}
        </p>
        {items.map((r) => (
          <details key={r.row_number} className={styles.expandable}>
            <summary>
              Row {r.row_number}: {r.raw_input}
            </summary>
            <div className={styles.expandableContent}>
              {r.issues
                .filter(
                  (i) =>
                    severity === 'Critical'
                      ? i.severity === 'Critical'
                      : true,
                )
                .map((issue, idx) => (
                  <div key={idx} style={{ marginBottom: '0.75rem' }}>
                    <div
                      className={
                        issue.severity === 'Critical'
                          ? styles.issueError
                          : styles.issueWarning
                      }
                    >
                      {issue.message}
                    </div>
                    <div className={styles.fix}>
                      <strong>Fix: </strong>
                      {issue.recommendation}
                    </div>
                    <div className={styles.fix}>
                      <strong>Retailer impact: </strong>
                      {issue.retailer_impact}
                    </div>
                  </div>
                ))}
            </div>
          </details>
        ))}
      </>
    )
  }

  return (
    <section id="issues" className={styles.section}>
      <h3>Issues by Severity</h3>
      {renderGroup(critical, 'Critical', 'CRITICAL', 'badge-critical', 'These GTINs will be rejected by retailers.')}
      {renderGroup(warning, 'Warning', 'WARNING', 'badge-warning', 'These GTINs may cause problems.')}
      {renderGroup(info, 'Info', 'INFO', 'badge-info', 'Best practice notes.')}
      {!critical.length && !warning.length && !info.length && (
        <div className={styles.success}>All GTINs passed validation with no issues!</div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Full Item Detail
// ---------------------------------------------------------------------------

export function FullItemDetail({ results }: { results: GTINResult[] }) {
  return (
    <section id="detail" className={styles.section}>
      <h3>Full Item Detail</h3>
      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Row</th>
              <th>GTIN</th>
              <th>Type</th>
              <th>Status</th>
              <th>Issues</th>
              <th>Corrected</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.row_number}>
                <td>{r.row_number}</td>
                <td style={{ fontFamily: 'monospace' }}>{r.raw_input}</td>
                <td>{r.gtin_type}</td>
                <td>
                  {!r.issues.length
                    ? 'Clean'
                    : r.has_critical
                      ? 'Critical'
                      : r.has_warning
                        ? 'Warning'
                        : 'Info'}
                </td>
                <td>{r.issues.length}</td>
                <td style={{ fontFamily: 'monospace' }}>{r.corrected_value || ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Check Digit Corrections
// ---------------------------------------------------------------------------

export function CheckDigitCorrections({
  items,
}: {
  items: BeforeAfter[]
}) {
  return (
    <section id="corrections" className={styles.section}>
      <h3>Check Digit Corrections</h3>
      <p>
        These GTINs have incorrect check digits. Always verify corrections
        against your original barcode or GS1 registration before updating your
        product master.
      </p>
      {items.length ? (
        <table>
          <thead>
            <tr>
              <th>Row</th>
              <th>Current (Before)</th>
              <th>Corrected (After)</th>
              <th>Issue</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.row}>
                <td>{item.row}</td>
                <td style={{ fontFamily: 'monospace' }}>{item.before}</td>
                <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{item.after}</td>
                <td>{item.issue}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className={styles.success}>
          No check digit corrections needed — all check digits are valid.
        </div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Packaging Hierarchy
// ---------------------------------------------------------------------------

export function PackagingHierarchy({
  hierarchy,
}: {
  hierarchy: HierarchyAnalysis
}) {
  return (
    <section id="hierarchy" className={styles.section}>
      <h3>Packaging Hierarchy Analysis</h3>
      <p>
        Retailers like Walmart require GTINs at every packaging level — each,
        inner pack, case, and pallet. This analysis checks whether your
        case-level GTIN-14s match up with unit-level GTINs.
      </p>

      {hierarchy.matched_pairs.length > 0 && (
        <>
          <h4>Matched unit &rarr; case pairs</h4>
          <table>
            <thead>
              <tr>
                <th>Case GTIN</th>
                <th>Case Row</th>
                <th>Unit GTIN</th>
                <th>Unit Row</th>
                <th>Indicator</th>
              </tr>
            </thead>
            <tbody>
              {hierarchy.matched_pairs.map((p, i) => (
                <tr key={i}>
                  <td style={{ fontFamily: 'monospace' }}>{p.case_gtin}</td>
                  <td>{p.case_row}</td>
                  <td style={{ fontFamily: 'monospace' }}>{p.unit_gtin}</td>
                  <td>{p.unit_row}</td>
                  <td>{p.indicator}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {hierarchy.orphan_cases.length > 0 && (
        <>
          <h4>Case GTINs without matching unit GTINs</h4>
          {hierarchy.orphan_cases.map((r) => (
            <p key={r.row_number} className={styles.issueWarning}>
              Row {r.row_number}: {r.cleaned} — no matching unit GTIN found
            </p>
          ))}
        </>
      )}

      {hierarchy.units_without_cases.length > 0 && (
        <>
          <h4>Unit GTINs without case-level GTINs</h4>
          <p className="text-muted">
            These items don't have a corresponding GTIN-14 for case/shipping
            identification.
          </p>
          {hierarchy.units_without_cases.map((r) => (
            <p key={r.row_number}>
              Row {r.row_number}: <strong>{r.cleaned}</strong> ({r.gtin_type})
            </p>
          ))}
        </>
      )}

      {!hierarchy.matched_pairs.length && !hierarchy.orphan_cases.length && (
        <div className={styles.success}>
          No GTIN-14 case-level codes found in your data. If you ship to Walmart
          or Costco, you'll likely need case GTINs.
        </div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Executive Summary
// ---------------------------------------------------------------------------

export function ExecutiveSummary({ text }: { text: string }) {
  return (
    <section id="summary" className={styles.section}>
      <h3>Executive Summary</h3>
      <p>Copy this summary and send it to your team. No jargon.</p>
      <div className={styles.summaryBox}>{text}</div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Prioritized Fix Plan
// ---------------------------------------------------------------------------

export function PrioritizedFixPlan({ items }: { items: FixRoadmapItem[] }) {
  return (
    <section id="roadmap" className={styles.section}>
      <h3>Prioritized Fix Plan</h3>
      <p>
        Issues ranked by impact x effort. Start at the top — these are your
        fastest wins with the biggest payoff.
      </p>
      {items.length ? (
        items.map((item, idx) => (
          <details key={item.code} className={styles.expandable}>
            <summary>
              Priority {idx + 1}: {item.action.slice(0, 80)}
              {item.action.length > 80 ? '...' : ''} ({item.count} item
              {item.count !== 1 ? 's' : ''})
            </summary>
            <div className={styles.expandableContent}>
              <div className={styles.roadmapMeta}>
                <div>
                  <strong>Effort</strong>
                  <span style={{ color: effortColor(item.effort) }}>
                    {item.effort}
                  </span>
                  <br />
                  <span className="text-xs">{item.effort_detail}</span>
                </div>
                <div>
                  <strong>Impact</strong>
                  <span style={{ color: impactColor(item.impact) }}>
                    {item.impact}
                  </span>
                  <br />
                  <span className="text-xs">{item.impact_detail}</span>
                </div>
                <div>
                  <strong>Time estimate</strong>
                  <span>{item.time_estimate}</span>
                </div>
              </div>
              <p>
                <strong>Full recommendation:</strong> {item.action}
              </p>
            </div>
          </details>
        ))
      ) : (
        <div className={styles.success}>No issues to fix — your data is clean!</div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Retailer Readiness
// ---------------------------------------------------------------------------

export function RetailerReadiness({
  checklists,
  selectedRetailer,
}: {
  checklists: Record<string, RetailerChecklist>
  selectedRetailer: string
}) {
  const entries =
    selectedRetailer !== 'All Retailers'
      ? [[selectedRetailer, checklists[selectedRetailer]] as const]
      : Object.entries(checklists)

  return (
    <section id="retailer" className={styles.section}>
      <h3>Retailer Submission Readiness</h3>
      <p>Each retailer has specific GTIN requirements. Here's how your data stacks up.</p>
      {entries.map(([name, checklist]) => {
        if (!checklist) return null
        const statusText = checklist.ready
          ? 'READY'
          : `${checklist.passed}/${checklist.total} checks passed`
        return (
          <div
            key={name}
            className={`${styles.retailerCard} ${checklist.ready ? styles.retailerReady : styles.retailerNotReady}`}
          >
            <strong>{name}</strong> &mdash;{' '}
            {checklist.ready ? '✓ ' : '✗ '}
            {statusText}
            <br />
            <span className="text-muted">{checklist.profile.description}</span>
            <div style={{ marginTop: '0.5rem' }}>
              {checklist.checks.map((c, i) => (
                <div key={i} className={styles.checkItem}>
                  {c.passed ? '✓' : '✗'} {c.check} — <em>{c.detail}</em>
                </div>
              ))}
            </div>
            {checklist.profile.notes && (
              <p className="text-xs" style={{ marginTop: '0.5rem' }}>
                {checklist.profile.notes}
              </p>
            )}
          </div>
        )
      })}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Cost of Inaction
// ---------------------------------------------------------------------------

export function CostOfInaction({ cost }: { cost: CostEstimate | null }) {
  if (!cost) {
    return (
      <section id="cost" className={styles.section}>
        <h3>Estimated Cost of Inaction</h3>
        <div className={styles.success}>No cost estimates — no issues detected.</div>
      </section>
    )
  }
  return (
    <section id="cost" className={styles.section}>
      <h3>Estimated Cost of Inaction</h3>
      <p>
        Based on industry averages for specialty food brands at similar scale.
        Directional, not predictive.
      </p>
      <div className={styles.costGrid}>
        <div className={styles.costCard}>
          <div className={styles.costNumber}>
            ${cost.annual_estimate_low.toLocaleString()} –{' '}
            ${cost.annual_estimate_high.toLocaleString()}
          </div>
          <div>Estimated annual cost of unresolved GTIN issues</div>
        </div>
        <div className={styles.costCard}>
          <div className={styles.costNumber}>{cost.rework_hours} hours/year</div>
          <div>Manual rework from GTIN problems</div>
        </div>
      </div>
      <h4>Breakdown</h4>
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Low Estimate</th>
            <th>High Estimate</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Chargebacks from invalid GTINs</td>
            <td>${cost.chargeback_range[0].toLocaleString()}</td>
            <td>${cost.chargeback_range[1].toLocaleString()}</td>
          </tr>
          <tr>
            <td>Delayed launches ({cost.delayed_skus} SKUs)</td>
            <td>${cost.delayed_launch_range[0].toLocaleString()}</td>
            <td>${cost.delayed_launch_range[1].toLocaleString()}</td>
          </tr>
          <tr>
            <td>Manual rework ({cost.rework_hours} hrs)</td>
            <td>${cost.rework_cost.toLocaleString()}</td>
            <td>${cost.rework_cost.toLocaleString()}</td>
          </tr>
        </tbody>
      </table>
      {cost.growth_note && (
        <p style={{ marginTop: '0.75rem', color: '#a05a1a', fontWeight: 500 }}>
          Growth multiplier: {cost.growth_note}
        </p>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Case GTIN Generator
// ---------------------------------------------------------------------------

export function CaseGTINGenerator({
  suggestions,
}: {
  suggestions: GTIN14Suggestion[]
}) {
  return (
    <section id="gtin14" className={styles.section}>
      <h3>Case GTIN-14 Generator</h3>
      <p>
        Unit-level GTINs that don't have a corresponding case-level GTIN-14.
        Below are the GTIN-14s you'd need to create for each packaging level.
      </p>
      {suggestions.length ? (
        <>
          <p>
            <strong>{suggestions.length} unit GTIN(s)</strong> need case-level
            GTIN-14s.
          </p>
          {suggestions.map((s) => (
            <details key={s.row} className={styles.expandable}>
              <summary>
                Row {s.row}: {s.unit_gtin} ({s.unit_type})
              </summary>
              <div className={styles.expandableContent}>
                <table>
                  <thead>
                    <tr>
                      <th>Indicator</th>
                      <th>GTIN-14</th>
                      <th>Packaging Level</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(s.indicators).map(([ind, info]) => (
                      <tr key={ind}>
                        <td>{ind}</td>
                        <td style={{ fontFamily: 'monospace' }}>{info.gtin14}</td>
                        <td>{info.label}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="text-xs" style={{ marginTop: '0.5rem' }}>
                  Most commonly, indicator 1 = case. Copy the GTIN-14 you need
                  and add it to your product master.
                </p>
              </div>
            </details>
          ))}
        </>
      ) : (
        <div className={styles.success}>
          All unit GTINs have matching case-level GTIN-14s, or no valid unit
          GTINs were found.
        </div>
      )}
    </section>
  )
}
