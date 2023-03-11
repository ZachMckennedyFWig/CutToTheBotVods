# Cut To The Bot Vods

This program aims to automate the parsing of Vex Robotics Competitions into individual matches by using text Object Character Recognition (OCR) to identify the starting and ending times of matches from the competition overlay. You can find the matches on the [Cut To The Bot Vods Youtube Channel](https://www.youtube.com/@CutToTheBotVod)

## Libraries Used: 
  - [OpenCV](https://github.com/opencv/opencv-python)
  - [tesserocr](https://github.com/sirfz/tesserocr)
 
 Additionally, [FFmpeg](https://ffmpeg.org/) must be installed on your computer. 
  
## Detailed Explaination

**Step 1:** Obtaining the match from VexTV

  Vex uses a service called [BoxCast](https://www.boxcast.com/) to host their live streaming website. All of their streams are played back as m3u8 streams, which can be thought of as a playlist of smaller videos. Getting the links to these streams could be automated with scraping, but since I do not have permission, I will show you how to manually get the link to them. 
  
  

