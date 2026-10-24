// DAFS Teaching App — anonymous deadline progress receiver.
//
// Paste this into a Google Sheet's Apps Script editor (Extensions > Apps Script),
// then deploy it as a Web App (see README.md "Monitoring student progress").
//
// Each time a student's app notices a configured deadline (see
// dafs_teach/content/deadlines.yaml) has passed, it POSTs one anonymous
// report here — no student name or other identifier is included, only
// per-exercise completed/attempts/solution_views counts. This script just
// appends the rows; there is nothing to upsert or de-duplicate by, since
// reports carry no identity to key on.

const SHEET_NAME = "Progress";
const HEADERS = [
  "deadline_id", "lesson_id", "lesson_title", "exercise_id",
  "completed", "attempts", "solution_views", "received_at",
];

function doPost(e) {
  const payload = JSON.parse(e.postData.contents);
  const deadlineId = payload.deadline_id;
  const rows = payload.rows || [];

  const sheet = getOrCreateSheet();
  const receivedAt = new Date().toISOString();

  const sheetRows = rows.map(function (row) {
    return [
      deadlineId,
      row.lesson_id,
      row.lesson_title || row.lesson_id,
      row.exercise_id,
      Number(row.completed),   // 0/1, not TRUE/FALSE, so SUM() works directly in Sheets formulas
      row.attempts,
      row.solution_views,
      receivedAt,
    ];
  });

  if (sheetRows.length > 0) {
    sheet.getRange(sheet.getLastRow() + 1, 1, sheetRows.length, HEADERS.length).setValues(sheetRows);
  }

  return ContentService
    .createTextOutput(JSON.stringify({ status: "ok", rows_received: sheetRows.length }))
    .setMimeType(ContentService.MimeType.JSON);
}

function getOrCreateSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(HEADERS);
    sheet.setFrozenRows(1);
  }
  return sheet;
}
