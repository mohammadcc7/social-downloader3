import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
import yt_dlp


# دالة لمعرفة مسار FFmpeg سواء كان البرنامج كود عادي أو ملف EXE مستقل
res_path = ""
if getattr(sys, 'frozen', False):
  res_path = sys._MEIPASS
else:
  res_path = os.path.dirname(os.path.abspath(__file__))

ffmpeg_path = os.path.join(res_path, 'ffmpeg.exe')


class SocialDownloaderApp:

  def __init__(self, root):
    self.root = root
    self.root.title("All-in-One Social Media Downloader")
    self.root.geometry("520x420")
    self.root.resizable(False, False)

    # عنوان التطبيق
    title_label = tk.Label(
        root, text="برنامج تحميل وسائل التواصل", font=("Arial", 16, "bold")
    )
    title_label.pack(pady=10)

    # حقل إدخال الرابط
    tk.Label(
        root,
        text="أدخل الرابط (يوتيوب، فيسبوك، انستغرام، تيك توك...):",
        font=("Arial", 11),
    ).pack(anchor="w", padx=30)
    self.url_entry = tk.Entry(root, font=("Arial", 11), width=52)
    self.url_entry.pack(pady=5, padx=30)

    # إضافة قائمة كليك يمين (نسخ، لصق، تحديد الكل) لحقل الإدخال
    self.create_context_menu(self.url_entry)

    # اختيار نوع التحميل (فيديو أو صوت)
    tk.Label(
        root, text="اختر صيغة التحميل:", font=("Arial", 11)
    ).pack(anchor="w", padx=30, pady=(10, 0))

    self.download_type = tk.StringVar(value="video")

    radio_frame = tk.Frame(root)
    radio_frame.pack(anchor="w", padx=30, pady=5)

    tk.Radiobutton(
        radio_frame,
        text="فيديو بجودة عالية (MP4)",
        variable=self.download_type,
        value="video",
        font=("Arial", 10),
    ).pack(side="left", padx=10)

    tk.Radiobutton(
        radio_frame,
        text="صوت فقط (MP3)",
        variable=self.download_type,
        value="audio",
        font=("Arial", 10),
    ).pack(side="left", padx=10)

    # زر التحميل
    self.download_btn = tk.Button(
        root,
        text="بدء التحميل",
        font=("Arial", 12, "bold"),
        bg="#1DA1F2",
        fg="white",
        width=20,
        command=self.start_download_thread,
    )
    self.download_btn.pack(pady=15)

    # شريط التقدم (Progress Bar)
    self.progress_bar = Progressbar(
        root, orient="horizontal", length=450, mode="determinate"
    )
    self.progress_bar.pack(pady=10)

    # حالة التحميل
    self.status_label = tk.Label(
        root, text="جاهز للتحميل...", font=("Arial", 10), fg="gray"
    )
    self.status_label.pack(pady=5)

  def create_context_menu(self, entry_widget):
    """إنشاء قائمة كليك يمين لحقول الإدخال"""
    menu = tk.Menu(entry_widget, tearoff=0)
    menu.add_command(
        label="قص",
        command=lambda: entry_widget.event_generate("<<Cut>>"),
    )
    menu.add_command(
        label="نسخ",
        command=lambda: entry_widget.event_generate("<<Copy>>"),
    )
    menu.add_command(
        label="لصق",
        command=lambda: entry_widget.event_generate("<<Paste>>"),
    )
    menu.add_separator()
    menu.add_command(
        label="تحديد الكل",
        command=lambda: entry_widget.select_range(0, tk.END),
    )

    def show_menu(event):
      menu.tk_popup(event.x_root, event.y_root)

    # ربط الأحداث بناءً على نظام التشغيل (زر الماوس الأيمن)
    if sys.platform.startswith('darwin'):
      entry_widget.bind("<Button-2>", show_menu)
    else:
      entry_widget.bind("<Button-3>", show_menu)

  def start_download_thread(self):
    url = self.url_entry.get().strip()
    if not url:
      messagebox.showerror("خطأ", "يرجى إدخال رابط صحيح!")
      return

    self.download_btn.config(state="disabled")
    self.progress_bar["value"] = 0
    self.status_label.config(text="جاري الاتصال بالرابط...", fg="blue")

    threading.Thread(target=self.download_content, args=(url,)).start()

  def progress_hook(self, d):
    if d['status'] == 'downloading':
      try:
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        if total > 0:
          percent = (downloaded / total) * 100
          self.root.after(
              0, lambda: self.update_progress(percent, f"جاري التحميل... {int(percent)}%")
          )
      except Exception:
        pass
    elif d['status'] == 'finished':
      self.root.after(
          0,
          lambda: self.update_progress(
              100, "جاري المعالجة والتحويل (إن وجد)..."
          ),
      )

  def update_progress(self, val, text):
    self.progress_bar["value"] = val
    self.status_label.config(text=text, fg="blue")

  def download_content(self, url):
    download_folder = filedialog.askdirectory(title="اختر مكان حفظ الملف")
    if not download_folder:
      self.root.after(0, self.reset_ui)
      return

    choice = self.download_type.get()

    try:
      ydl_opts = {
          'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
          'progress_hooks': [self.progress_hook],
      }

      if os.path.exists(ffmpeg_path):
        ydl_opts['ffmpeg_location'] = ffmpeg_path

      if choice == "video":
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
      else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

      self.root.after(
          0, lambda: messagebox.showinfo("نجاح", "تم التحميل بنجاح!")
      )
      self.root.after(
          0,
          lambda: self.status_label.config(
              text="اكتمل التحميل بنجاح!", fg="green"
          ),
      )

    except Exception as e:
      self.root.after(
          0,
          lambda: messagebox.showerror(
              "خطأ", f"حدث خطأ أثناء التحميل:\n{str(e)}"
          ),
      )
      self.root.after(
          0, lambda: self.status_label.status_label.config(text="فشل التحميل", fg="red") if hasattr(self.status_label, 'status_label') else self.status_label.config(text="فشل التحميل", fg="red")
      )

    finally:
      self.root.after(0, self.reset_ui)

  def reset_ui(self):
    self.download_btn.config(state="normal")


if __name__ == "__main__":
  root = tk.Tk()
  app = SocialDownloaderApp(root)
  root.mainloop()
