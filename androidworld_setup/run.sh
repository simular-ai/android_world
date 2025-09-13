#!/bin/bash

# Optional: start emulator (uncomment if needed)
# ~/Library/Android/sdk/emulator/emulator -avd AndroidWorld -no-snapshot -grpc 8554

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Static task list (one per line). Add/remove as needed.
TASKS=(
  AudioRecorderRecordAudio
  AudioRecorderRecordAudioWithFileName
  BrowserDraw
  BrowserMaze
  BrowserMultiply
  CameraTakePhoto
  CameraTakeVideo
  ClockStopWatchPausedVerify
  ClockStopWatchRunning
  ClockTimerEntry
  ContactsAddContact
  ContactsNewContactDraft
  ExpenseAddMultiple
  ExpenseAddMultipleFromGallery
  ExpenseAddMultipleFromMarkor
  ExpenseAddSingle
  ExpenseDeleteDuplicates
  ExpenseDeleteDuplicates2
  ExpenseDeleteMultiple
  ExpenseDeleteMultiple2
  ExpenseDeleteSingle
  FilesDeleteFile
  FilesMoveFile
  MarkorAddNoteHeader
  MarkorChangeNoteContent
  MarkorCreateFolder
  MarkorCreateNote
  MarkorCreateNoteAndSms
  MarkorCreateNoteFromClipboard
  MarkorDeleteAllNotes
  MarkorDeleteNewestNote
  MarkorDeleteNote
  MarkorEditNote
  MarkorMergeNotes
  MarkorMoveNote
  MarkorTranscribeReceipt
  MarkorTranscribeVideo
  NotesIsTodo
  NotesMeetingAttendeeCount
  NotesRecipeIngredientCount
  NotesTodoItemCount
  OpenAppTaskEval
  OsmAndFavorite
  OsmAndMarker
  OsmAndTrack
  RecipeAddMultipleRecipes
  RecipeAddMultipleRecipesFromImage
  RecipeAddMultipleRecipesFromMarkor
  RecipeAddMultipleRecipesFromMarkor2
  RecipeAddSingleRecipe
  RecipeDeleteDuplicateRecipes
  RecipeDeleteDuplicateRecipes2
  RecipeDeleteDuplicateRecipes3
  RecipeDeleteMultipleRecipes
  RecipeDeleteMultipleRecipesWithConstraint
  RecipeDeleteMultipleRecipesWithNoise
  RecipeDeleteSingleRecipe
  RecipeDeleteSingleWithRecipeWithNoise
  RetroCreatePlaylist
  RetroPlayingQueue
  RetroPlaylistDuration
  RetroSavePlaylist
  SaveCopyOfReceiptTaskEval
  SimpleCalendarAddOneEvent
  SimpleCalendarAddOneEventInTwoWeeks
  SimpleCalendarAddOneEventRelativeDay
  SimpleCalendarAddOneEventTomorrow
  SimpleCalendarAddRepeatingEvent
  SimpleCalendarAnyEventsOnDate
  SimpleCalendarDeleteEvents
  SimpleCalendarDeleteEventsOnRelativeDay
  SimpleCalendarDeleteOneEvent
  SimpleCalendarEventOnDateAtTime
  SimpleCalendarEventsInNextWeek
  SimpleCalendarEventsInTimeRange
  SimpleCalendarEventsOnDate
  SimpleCalendarFirstEventAfterStartTime
  SimpleCalendarLocationOfEvent
  SimpleCalendarNextEvent
  SimpleCalendarNextMeetingWithPerson
  SimpleDrawProCreateDrawing
  SimpleSmsReply
  SimpleSmsReplyMostRecent
  SimpleSmsResend
  SimpleSmsSend
  SimpleSmsSendClipboardContent
  SimpleSmsSendReceivedAddress
  SportsTrackerActivitiesCountForWeek
  SportsTrackerActivitiesOnDate
  SportsTrackerActivityDuration
  SportsTrackerLongestDistanceActivity
  SportsTrackerTotalDistanceForCategoryOverInterval
  SportsTrackerTotalDurationForCategoryThisWeek
  SystemBluetoothTurnOff
  SystemBluetoothTurnOffVerify
  SystemBluetoothTurnOn
  SystemBluetoothTurnOnVerify
  SystemBrightnessMax
  SystemBrightnessMaxVerify
  SystemBrightnessMin
  SystemBrightnessMinVerify
  SystemCopyToClipboard
  SystemWifiTurnOff
  SystemWifiTurnOffVerify
  SystemWifiTurnOn
  SystemWifiTurnOnVerify
  TasksCompletedTasksForDate
  TasksDueNextWeek
  TasksDueOnDate
  TasksHighPriorityTasks
  TasksHighPriorityTasksDueOnDate
  TasksIncompleteTasksOnDate
  TurnOffWifiAndTurnOnBluetooth
  TurnOnWifiAndOpenApp
)
#   VlcCreatePlaylist
#   VlcCreateTwoPlaylists

# If a single task is provided as an argument, override TASKS
if [[ $# -gt 0 ]]; then
  TASKS=("$1")
fi

for name in "${TASKS[@]}"; do
  RESULTS_DIR="$SCRIPT_DIR/results/$name"
  if [[ -f "$RESULTS_DIR/result.txt" ]]; then
    echo "Skipping $name (already completed)."
    continue
  fi
  if [[ -d "$RESULTS_DIR" ]]; then
    echo "Cleaning stale results: $RESULTS_DIR"
    rm -rf "$RESULTS_DIR"
  fi
  echo "\n=== Running task: $name ==="
  python "$SCRIPT_DIR/run_android_env.py" --task="$name"
  echo "--- Finished task: $name ---"
done
