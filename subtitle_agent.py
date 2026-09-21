def format_srt_time(seconds):
    """Formats seconds into SRT time format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_srt(dialogues, durations, output_file):
    """
    Generate an SRT file based on a list of dialogues and their corresponding audio durations.
    """
    current_time = 0.0
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, (dialogue, duration) in enumerate(zip(dialogues, durations)):
            start_time_str = format_srt_time(current_time)
            end_time = current_time + duration
            end_time_str = format_srt_time(end_time)
            
            f.write(f"{i + 1}\n")
            f.write(f"{start_time_str} --> {end_time_str}\n")
            # Write the text (wrap if too long, or just write directly)
            f.write(f"{dialogue['text']}\n\n")
            
            current_time = end_time
    return output_file
