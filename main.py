import subprocess
import cv2
import tesserocr 
import json

'''
To run this program all you need to do is paste the the m3u8 link from VexTV of the livestream to the url variable and manually type in the division name 
    so that is able to correctly identify matches. 
'''

url = 'Enter m3u8 link here'
DIVISION_NAME = 'Enter div name here'

'''
**********************************************************************************************************************************************************
'''


def frame_at_time(time_stamp):
    """
        Function to grab the frame from the m3u8 stream at the given timestamp

        time_stamp: time in seconds 
    """
    output_file = 'TempImages/frame.jpg'                                        # Set the output file name and image format
    options = ['-ss', str(time_stamp), '-copyts', '-y', '-i', url,
                '-frames:v', '1', '-q:v', '1', output_file, '-hide_banner',     # Set the FFmpeg command options
                '-loglevel', 'error']
    check = subprocess.run(['ffmpeg'] + options)                                # Run the ffmpeg command to grab the frame at the given timestamp
    return check                                                                # Returns the output of the ffmpeg command (to check if we are outside the video range)


def grab_match_info(qual=True, div=True):
    """
        Function to pull out the qual number and division from the captured frame

        qual: True if you want it to grab the qual number image
        div: True if you want it to gran the division image
    """
    frame = cv2.imread('TempImages/frame.jpg')              # Reads in the image to a variable
    frame = cv2.bitwise_not(frame)                          # Inverts the image to make the text black
    frame = cv2.convertScaleAbs(frame, alpha=3.0, beta=0)   # Scales up brightness to attempt to make the entire background white

    if qual:
        temp = frame[27:83, 595:805]                                                            # Grabs the part of the frame with the qual number 
        temp = cv2.copyMakeBorder(temp, 20, 20, 0, 0, cv2.BORDER_CONSTANT, value=(255,255,255)) # Makes a boarder around the resulting image, this is because 
                                                                                                #   text OCR struggles if the text is very close to the edge
                                                                                                #   of the image because of how they are trained. 
        cv2.imwrite('TempImages/QualNumber.jpg', temp)                                          # Save the cropped image of the qual number

    if div:
        cv2.imwrite('TempImages/Division.jpg', frame[5:80, 820:1090])                           # Save the cropped image of the division


def get_cur_match():
    """
        Function to grab the current qual number out of the saved image
    """

    alt_text = ['R16', 'QF', 'SF', 'F']                                             # Array to store the possible combinations of elims acronyms 

    match_val = tesserocr.file_to_text('TempImages/QualNumber.jpg', psm=6).strip()  # Performs OCR on the match number image, psm 6 is a setting that
                                                                                    #   tells the OCR to look for a single line, single word set of characters
    if match_val.isdigit():                                                         # Checks if the OCR returned a number, this would mean its a qual match
        return int(match_val)                                                       #   In that case, just return the qual number
    elif len(match_val) > 3:                                                        # Either QF, SF, or RO16
        elim_val = match_val.split()                                                #   OCR correctly identifies these matches with a space between the prefix
                                                                                    #       and the number, split out the number and prefix
        if elim_val[0] in alt_text:                                                 #   Double checks its actually a elim match with the possible acronyms list
                                                                                    #       because random noise could somehow possibly get past the last couple steps. 
            return f"{elim_val[0]} #{elim_val[1]}"                                  #   Return the formatted Match title
        else:
            return ''
    elif 'F' in match_val:                                                          # Because OCR sometimes messes up Finals, this solves the edge case
        match_val = match_val.replace(' ', '')                                      #   sometimes it puts a space between the F and number, sometimes it doesn't 
        if match_val[1].isdigit():                                                  # If the second character is a number, this double checks its valid
            return f'Final #1-{match_val[1]}'                                       # Returns the formatted match title
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

    is_qual = True      # Variable used to to change file named depending on qual vs elims match
    match_bounds = {}   # Dict to store the match info when parsed from the json files
    cur_time = 0        # Start time in the m3u8 file in seconds. 

    while True:
        print(cur_time)
        temp = frame_at_time(cur_time)  # Saves the frame at the current timestamp

        if temp.returncode != 0:        # Weird way to find the end of the stream... oh well
            print("reached the end")
            break
        
        grab_match_info(qual = False)   # Grab the Division image out of the frame
        div_name = get_cur_div()        # Gets the division name from that image

        if div_name == DIVISION_NAME:       # Checks to make sure the division name and the manually entered name are the same 
            grab_match_info(div = False)    # Grabs the match number image from the frame
            match_val = get_cur_match()     # From that image, gets the actual match number 

            if match_val != '':                                                             # If the match is valid

                f = open(f'DivResults/{DIVISION_NAME}DivResults.json')                      # Open the json for the divison results
                results = json.load(f)                                                      # Load the json for that division results

                if isinstance(match_val, int):
                    is_qual = True
                    blue_alliance = results['data'][match_val-1]['alliances'][0]            # Preload Blue alliance info
                    red_alliance = results['data'][match_val-1]['alliances'][1]             # Preload Red alliance info
                else:
                    is_qual = False
                    match_dict = list(filter(lambda elims: elims['name'] == f'{match_val}', results['data']))[0]    # For elims matches, manually search the json for those 
                                                                                                                    #   results since they are not in order like the quals. 
                    blue_alliance = match_dict['alliances'][0]                              # Preload Blue alliance info
                    red_alliance = match_dict['alliances'][1]                               # Preload Red alliance info

                blue_teams = [team['team']['name'] for team in blue_alliance['teams']]      # Grab the blue team numbers and score
                blue_score = blue_alliance['score']

                red_teams = [team['team']['name'] for team in red_alliance['teams']]        # Grab the red team numbers and score
                red_score = red_alliance['score']

                match_bounds = {'start': cur_time, 'qual': match_val, 'blue_teams': blue_teams, 
                                    'blue_score': blue_score, 'red_teams': red_teams, 
                                    'red_score': red_score}                               # Start setting the information for this match into the dict 

                print(blue_teams, blue_score)
                print(red_teams, red_score)

                cur_time += 120                             # Skip ahead 2 minutes in the stream (minimum length of match)

                temp = frame_at_time(cur_time)              # Grabs the new frame at that time
                grab_match_info(div = False)                # Grabs the match number from the new frame
                new_match_val = get_cur_match()

                if match_val == new_match_val:              # If it is still the same match
                    while match_val == new_match_val:       # Loop until it is no longer that match
                        cur_time += 5
                        temp = frame_at_time(cur_time)
                        grab_match_info(div = False)
                        new_match_val = get_cur_match()      

                    match_bounds['end'] = cur_time          # Sets the ending time of this match

                    if is_qual:                             # Depending on qual vs. elims match, sets the file name for the matches and saves them using ffmpeg. 
                        file_name = f'\"CutVideos/2022 VRC-HS {DIVISION_NAME} Q{match_bounds["qual"]} - {" ".join(match_bounds["red_teams"])} vs {" ".join(match_bounds["blue_teams"])} - {match_bounds["red_score"]} to {match_bounds["blue_score"]}.mp4\"'
                    else:
                        file_name = f'\"CutVideos/2022 VRC-HS {DIVISION_NAME} {match_bounds["qual"]} - {" ".join(match_bounds["red_teams"])} vs {" ".join(match_bounds["blue_teams"])} - {match_bounds["red_score"]} to {match_bounds["blue_score"]}.mp4\"'

                    print(match_bounds)
                    ffmpeg_command = f"ffmpeg -ss {match_bounds['start']} -i {url} -t {match_bounds['end'] - match_bounds['start']} -c copy {file_name} -y -hide_banner -loglevel error" 
                    subprocess.call(ffmpeg_command)
                else:
                    cur_time -= 115     # If its not the same match after the 2 minute skip, it was probably a production error on the livestream and was the incorrect match anyways. Go back to 5 seconds ahead. 
            else:
                cur_time += 5  
        else:
            cur_time += 5                        