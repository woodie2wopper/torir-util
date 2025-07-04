using terms from application "Mail"
	--save selected messages to text files
	on perform mail action with messages messageList
		set theFolder to choose folder with prompt "Save Exported Messages to..." without invisibles
		set the message_count to the count of messageList
		display dialog "Found " & (message_count) & " messages."
		repeat with i from 1 to the message_count
			set this_message to item i of messageList
			set theFile to (((theFolder) as Unicode text) & (i) as Unicode text) & ".txt"
			set theSubject to subject of this_message
			set theDate to date received of this_message
			set theSender to sender of this_message
			set theContent to (content of this_message) as Unicode text
			set headerText to "From: " & theSender & return & "Date: " & theDate & return & "Subject: " & theSubject & return & return
			
			try
				set theFileID to open for access theFile with write permission
				write headerText & theContent to theFileID
				close theFileID
			on error
				display dialog "Can't write message"
			end try
			
		end repeat
		display dialog "Done exporting " & (message_count) & " messages."
	end perform mail action with messages
end using terms from

using terms from application "Mail"
	on run
		tell application "Mail" to set mySelection to selection
		tell me to perform mail action with messages (mySelection)
	end run
end using terms from