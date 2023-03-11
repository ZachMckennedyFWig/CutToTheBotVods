import subprocess
import cv2
import tesserocr 
import json

url = 'Enter m3u8 link here'
DIVISION_NAME = 'Enter div name here'

def frame_at_time(time_stamp):
    """
        Function to grab the frame from the m3u8 stream at the given timestamp

        time_stamp: time in seconds 
    """
    # Set the output file name and format
    output_file = 'TempImages/frame.jpg'
    # Set the FFmpeg command options
    options = ['-ss', str(time_stamp), '-copyts', '-y', '-i', url, '-frames:v', '1', '-q:v', '1', output_file, '-hide_banner', '-loglevel', 'error']
    check = subprocess.run(['ffmpeg'] + options)
    return check


def grab_match_info(qual=True, div=True):
    """
        Function to pull out the qual number and division from the captured frame

        qual: True if you want it to grab the qual number image
        div: True if you want it to gran the division image
    """
    frame = cv2.imread('TempImages/frame.jpg')
    frame = cv2.bitwise_not(frame)
    frame = cv2.convertScaleAbs(frame, alpha=3.0, beta=0)

    if qual:
        temp = frame[27:83, 595:805]
        temp = cv2.copyMakeBorder(temp, 20, 20, 0, 0, cv2.BORDER_CONSTANT, value=(255,255,255))
        cv2.imwrite('TempImages/QualNumber.jpg', temp) # Write the cropped image of the qual number

    if div:
        cv2.imwrite('TempImages/Division.jpg', frame[5:80, 820:1090])  # Write the cropped image of the division


def get_cur_match():
    """
        Function to grab the current qual number out of the saved image
    """

    alt_text = ['R16', 'QF', 'SF', 'F']

    match_val = tesserocr.file_to_text('TempImages/QualNumber.jpg', psm=6).strip()

    if match_val.isdigit():
        return int(match_val)
    elif len(match_val) > 3:  # Either QF, SF, or RO16
        elim_val = match_val.split()
        if elim_val[0] in alt_text:    # Double checks its actually a elim match
            return f"{elim_val[0]} #{elim_val[1]}"
        else:
            return ''
    elif 'F' in match_val:  # Because OCR sometimes messes up Finals, this solves the edge case
        match_val = match_val.replace(' ', '')
        if match_val[1].isdigit():
            return f'Final #1-{match_val[1]}'
        else:
            return ''
    else:
        return ''


def get_cur_div():
    """
        Function to return the current division name out of the saved image, doesn't need to be a function but made this
            to be consistent with get_cur_match. 
    """
    div_name = tesserocr.file_to_text('TempImages/Division.jpg', psm=6).strip() # Grab the division name
    return div_name

    
if __name__ == "__main__":

    is_qual = True
    match_bounds = {}
    cur_time = 25290

    while True:
        print(cur_time)
        temp = frame_at_time(cur_time)

        if temp.returncode != 0:        # Weird way to find the end of the stream... oh well
            print("reached the end")
            break
        
        grab_match_info(qual = False)   # Grab the Division image out of the frame
        div_name = get_cur_div()

        if div_name == DIVISION_NAME:
            grab_match_info(div = False)

            match_val = get_cur_match()

            if match_val != '':

                f = open(f'DivResults/{DIVISION_NAME}DivResults.json')                      # Open the json for the divison
                results = json.load(f)                                                      # Load the json for that division

                if isinstance(match_val, int):
                    is_qual = True
                    blue_alliance = results['data'][match_val-1]['alliances'][0]                 # Preload Blue alliance
                    red_alliance = results['data'][match_val-1]['alliances'][1]                  # Preload Red alliance
                else:
                    is_qual = False
                    match_dict = list(filter(lambda elims: elims['name'] == f'{match_val}', results['data']))[0]
                    blue_alliance = match_dict['alliances'][0]
                    red_alliance = match_dict['alliances'][1]

                blue_teams = [team['team']['name'] for team in blue_alliance['teams']]      # Grab the blue teams and score
                blue_score = blue_alliance['score']

                red_teams = [team['team']['name'] for team in red_alliance['teams']]        # Grab the red teams and score
                red_score = red_alliance['score']

                match_bounds = {'start': cur_time, 'qual': match_val, 'blue_teams': blue_teams, 
                                    'blue_score': blue_score, 'red_teams': red_teams, 
                                    'red_score': red_score}                               # Start setting the information for this match

                print(blue_teams, blue_score)
                print(red_teams, red_score)

                cur_time += 120 # Skip ahead 2 minutes (minimum length of match)

                temp = frame_at_time(cur_time)
                grab_match_info(div = False)
                new_match_val = get_cur_match()

                if match_val == new_match_val:
                    while match_val == new_match_val:
                        cur_time += 5
                        temp = frame_at_time(cur_time)
                        grab_match_info(div = False)
                        new_match_val = get_cur_match()      

                    match_bounds['end'] = cur_time     # Sets the ending time of this match

                    if is_qual:
                        file_name = f'\"CutVideos/2022 VRC-HS {DIVISION_NAME} Q{match_bounds["qual"]} - {" ".join(match_bounds["red_teams"])} vs {" ".join(match_bounds["blue_teams"])} - {match_bounds["red_score"]} to {match_bounds["blue_score"]}.mp4\"'
                    else:
                        file_name = f'\"CutVideos/2022 VRC-HS {DIVISION_NAME} {match_bounds["qual"]} - {" ".join(match_bounds["red_teams"])} vs {" ".join(match_bounds["blue_teams"])} - {match_bounds["red_score"]} to {match_bounds["blue_score"]}.mp4\"'

                    print(match_bounds)
                    ffmpeg_command = f"ffmpeg -ss {match_bounds['start']} -i {url} -t {match_bounds['end'] - match_bounds['start']} -c copy {file_name} -y -hide_banner -loglevel error"

                    subprocess.call(ffmpeg_command)
                else:
                    cur_time -= 115
            else:
                cur_time += 5  
        else:
            cur_time += 5                        