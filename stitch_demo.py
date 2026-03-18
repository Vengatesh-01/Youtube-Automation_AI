import os
from moviepy.editor import ImageSequenceClip, AudioFileClip

def stitch(image_folder, audio_path, output_path, fps=24):
    # Get all PNGs
    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    images.sort()
    
    full_images = [os.path.join(image_folder, img) for img in images]
    
    if not full_images:
        print(f"No images found in {image_folder} to stitch!")
        return False

    print(f"Stitching {len(full_images)} frames...")
    clip = ImageSequenceClip(full_images, fps=fps)
    
    if audio_path and os.path.exists(audio_path):
        audio = AudioFileClip(audio_path)
        clip = clip.set_audio(audio)
    
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    print(f"✅ Video created at: {output_path}")
    return True

if __name__ == "__main__":
    stitch()
