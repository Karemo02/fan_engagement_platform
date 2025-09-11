import requests  # Import requests for HTTP
import json  # Import json for data
import re  # Import re for regex

# Configuration
base_url = 'http://127.0.0.1:8000'  # Set base URL
login_url = f'{base_url}/engagement/login/'  # Set login URL
sentiment_url = f'{base_url}/engagement/api/analyze-sentiment/'  # Set sentiment URL
credentials = {'username': 'testuser', 'password': 'pass111'}  # Set test credentials

# Step 1: Get initial CSRF token from login page
session = requests.Session()  # Create session
response = session.get(login_url)  # Get login page
if response.status_code != 200:  # Check response
    print(f"Failed to access login page: {response.status_code} - {response.text}")  # Print error
    exit()  # Exit on failure

# Extract CSRF token from cookies or HTML
csrf_token = session.cookies.get('csrftoken')  # Get CSRF from cookies
if not csrf_token:  # If no token
    csrf_token_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)  # Search HTML
    if csrf_token_match:  # If found
        csrf_token = csrf_token_match.group(1)  # Extract token
    if not csrf_token:  # If still missing
        print("CSRF token not found in cookies or HTML. Check login page response.")  # Print error
        exit()  # Exit on failure

# Step 2: Log in to get authenticated session
login_data = {  # Prepare login data
    'username': credentials['username'],  # Set username
    'password': credentials['password'],  # Set password
    'csrfmiddlewaretoken': csrf_token  # Set CSRF token
}
headers = {  # Set headers
    'Content-Type': 'application/x-www-form-urlencoded',  # Set content type
    'X-CSRFToken': csrf_token,  # Set CSRF header
    'Referer': login_url  # Set referer
}
login_response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)  # Post login

# Debug login response
print(f"Login response status: {login_response.status_code}")  # Print status
print(f"Login response URL: {login_response.url}")  # Print URL
print(f"Login response text (first 500 chars): {login_response.text[:500]}...")  # Print response
print(f"Response cookies: {dict(session.cookies)}")  # Print cookies

# Check if login was successful
if login_response.status_code == 302:  # Check redirect
    print("Login redirected, checking destination...")  # Print redirect
    final_url = login_response.url  # Get final URL
    if '/engagement/' in final_url or '/accounts/profile/' in final_url:  # Check destination
        print(f"Login successful, redirected to: {final_url}")  # Print success
    else:
        print(f"Unexpected redirect to: {final_url}")  # Print error
        exit()  # Exit on failure
elif login_response.status_code == 200 and 'login' not in login_response.url:  # Check no redirect
    print("Login successful, no redirect needed.")  # Print success
else:
    print(f"Login failed: {login_response.status_code} - {login_response.text}")  # Print failure
    exit()  # Exit on failure

# Update CSRF token and check session cookies
csrf_token = session.cookies.get('csrftoken')  # Update CSRF
session_cookie = session.cookies.get('sessionid')  # Get session ID
if not csrf_token or not session_cookie:  # Check tokens
    print("Post-login CSRF token or sessionid not found. Authentication may have failed.")  # Print error
    print(f"CSRF token: {csrf_token}")  # Print CSRF
    print(f"Session cookie: {session_cookie}")  # Print session
    exit()  # Exit on failure

print(f"Post-login CSRF token: {csrf_token}")  # Print CSRF
print(f"Session cookie: {session_cookie}")  # Print session

# Step 3: Test sentiment analysis with 300 comments
comments = [ # Define test comments
    "What a rollercoaster of a match! So proud of how we fought back.",
    "Honestly, the referee made a mess of that game.",
    "Incredible atmosphere at the stadium tonight — goosebumps!",
    "We dominated possession but couldn’t finish. Frustrating.",
    "That young midfielder is going to be a star in a few years.",
    "Defensive errors killed us again. Can’t keep giving away cheap goals.",
    "Best win of the season, no doubt. The boys showed real heart.",
    "Not sure about the manager’s subs. Didn’t make sense tactically.",
    "The fans were absolutely electric. Love this community.",
    "Missed chances come back to haunt you — simple as that.",
    "Sadio Mane was everywhere today. What a performance!",
    "Still unbeaten in six. Momentum is building.",
    "Penalty should’ve been given. Clear handball.",
    "Keeper made two world-class saves. Man of the match for me.",
    "Midfield was completely overrun. Needs serious improvement.",
    "Can’t believe we dropped points at home again.",
    "The chemistry between the front two is looking dangerous.",
    "Set pieces are a nightmare. We’re too predictable.",
    "Pep’s tactics were spot on today. Outsmarted the opposition.",
    "First clean sheet in ages. Defense finally clicked.",
    "VAR needs a serious review. This is getting ridiculous.",
    "Absolute worldie from outside the box! What a goal!",
    "Too many individual mistakes. Can’t win titles like this.",
    "So happy to see the new signing adapting so quickly.",
    "Refused to give up even when down two. That’s character.",
    "The pace of the game was insane. Non-stop action.",
    "Not impressed with the bench options. Lacked impact.",
    "That assist from Trent was pure vision.",
    "Huge three points in the title race. Massive win.",
    "Didn’t expect us to win, but we took our chances well.",
    "The yellow card in the 38th minute changed the game.",
    "Our fullbacks are leaving too much space. Opponents are exploiting it.",
    "Goal celebration was fire! Love the squad vibes.",
    "Tactically, we were all over the place. No structure.",
    "Youngster on debut scored! Dream come true moment.",
    "Passing in the final third was so slick today.",
    "Need to work on set-piece defending. Again.",
    "Counterattacks were deadly. Used the wings perfectly.",
    "Disappointed with the draw. We deserved more.",
    "Injury to the captain is a huge blow for next week.",
    "The crowd lifted the team in the second half.",
    "Overrated performance. Lucky to get the win.",
    "Substitute made an immediate impact. Perfect change.",
    "Backline held strong under pressure. Solid effort.",
    "Missed penalty in the 90th minute — gutting.",
    "That through ball was perfectly weighted. Genius.",
    "Too many long balls. We’re not playing our style.",
    "Player of the match without a doubt. Worked his socks off.",
    "Final 15 minutes were pure chaos. Can’t watch like this.",
    "They scored from their only shot. Tough to take.",
    "Team looked tired in the second half. Rotation needed.",
    "Unbelievable technique on that free kick!",
    "Defensive midfield role needs more discipline.",
    "Great team goal, built from the back. Loved it.",
    "Frustrating offside call killed a great move.",
    "Captain’s speech after the game gave me chills.",
    "Should’ve had a red card. Dangerous tackle.",
    "Winger was unstoppable today. Constant threat.",
    "Possession without purpose. Just sideways passes.",
    "So proud to wear this jersey. What a club.",
    "Tactical masterclass. Controlled every phase.",
    "Not enough creativity in attack. Too predictable.",
    "Weather made it messy, but both teams gave it their all.",
    "Young defender stepped up big time. Future looks bright.",
    "Late goal broke my heart. So close.",
    "Celebrated like we won the league. It’s just three points.",
    "Consistency is the biggest issue this season.",
    "Corner routines finally worked. About time.",
    "Opponent played with more intensity. We matched it.",
    "Midfield trio controlled the tempo beautifully.",
    "One moment of magic changed the whole game.",
    "Lack of communication in defense cost us.",
    "Keeper’s distribution was excellent today.",
    "Hard-fought point on the road. Take it.",
    "Booking in the first half hurt our rhythm.",
    "Crossing was awful. Wasted so many chances.",
    "Injury-time winner! Stadium went wild!",
    "Tired legs in extra time. Understandable.",
    "Formation change paid off. More balance.",
    "Supporters sang the whole match. Amazing energy.",
    "Too many fouls in dangerous areas. Asking for trouble.",
    "Clinical finishing. Took every chance.",
    "Missed the target from three yards out. How?",
    "Calm and composed under pressure. Grown so much.",
    "Red card was harsh, but the tackle was risky.",
    "We’ve turned a corner. Confidence is back.",
    "Tactical foul in the 89th minute saved the draw.",
    "Full team effort. Nobody took a step back.",
    "Substitute goalkeeper made a crucial save. Hero.",
    "Passing accuracy was over 90%. Impressive.",
    "Not the result we wanted, but there are positives.",
    "Left-back overlapped perfectly all game.",
    "So disappointed with the disciplinary record.",
    "Game had everything — goals, drama, passion.",
    "Player got booked for diving. Felt harsh.",
    "Team spirit is through the roof right now.",
    "Final whistle brought tears. Emotional win.",
    "We need a proper striker. This isn’t working.",
    "Clean sheet feels like a victory today.",
    "Manager’s post-match interview was very honest.",
    "Long ball over the top caught them sleeping.",
    "Second goal was offside. VAR missed it.",
    "Youth academy is producing gems. Watch this space.",
    "Scoreline doesn’t reflect the performance.",
    "Pressure in the final third was relentless.",
    "Missed a golden chance in the first half.",
    "Defender scored from a corner! Unbelievable.",
    "Team looked disjointed. No cohesion.",
    "Counter-pressing was on point today.",
    "So proud of the comeback. Never say die attitude.",
    "Ref used the mic to explain a decision. Respect.",
    "Too many turnovers in midfield.",
    "Captain lifted the trophy with tears in his eyes.",
    "Fan banners were incredible. True passion.",
    "Late equalizer felt like a win.",
    "Need more from the wide players.",
    "Goalkeeper’s positioning was perfect.",
    "It’s not just about winning — it’s how we play.",
    "Player received a standing ovation. Deserved.",
    "Rain didn’t stop the fans. Amazing support.",
    "Backheel pass in the box was pure class.",
    "Settled into the game after a shaky start.",
    "Opposition keeper was the difference.",
    "First-half performance was embarrassing.",
    "Tactical flexibility won us the match.",
    "One player carried the team today.",
    "Couldn’t handle their physicality.",
    "Build-up play was patient and intelligent.",
    "Final ball was missing all night.",
    "Dug deep when it mattered most.",
    "Celebrated with the fans. Beautiful moment.",
    "Rotation policy paying off with fresh legs.",
    "So many injuries lately. Bad luck.",
    "They played with ten men for 30 minutes but still won.",
    "Discipline and focus for 90 minutes. Perfect.",
    "Missed penalty early on set the tone.",
    "Youngster’s composure on the ball was impressive.",
    "Team looked nervous from the first whistle.",
    "Crossbar save in the 88th minute! Unbelievable.",
    "We’ve got a new cult hero after tonight.",
    "Tactical foul stopped a dangerous attack.",
    "Formation gave us control in midfield.",
    "Player apologized to fans after mistake. Class act.",
    "Stadium was packed. Great turnout.",
    "Long-range effort almost went in.",
    "Kept their shape even under pressure.",
    "Final pass lacked quality.",
    "So happy for the manager. Needed this win.",
    "Defensive line pushed up too high.",
    "Substitute scored within two minutes. Impact player.",
    "Match was end-to-end. No time to breathe.",
    "Player got a yellow for time-wasting.",
    "Team showed maturity in the second half.",
    "Keeper palmed it over the bar. Huge moment.",
    "We’re playing with more belief now.",
    "Missed chance in stoppage time. Heartbreaking.",
    "Solid performance, but lacked spark.",
    "Captain led by example again.",
    "Player received racist abuse online after the game. Disgusting.",
    "Tactical awareness from the coach was excellent.",
    "Backheel flick in the box was unreal.",
    "Scored from a corner routine we’ve practiced all week.",
    "Team didn’t give up despite being a man down.",
    "Final whistle brought relief more than joy.",
    "Player went down injured. Hope it’s not serious.",
    "So proud of the unity in the squad.",
    "Opposition had more desire.",
    "Passing lanes were closed down quickly.",
    "Emotional night for the club. Legend retired.",
    "Player celebrated with a tribute. Touching moment.",
    "Need to convert dominance into goals.",
    "Team adapted well to the red card.",
    "Midfield battle was won decisively.",
    "Fan choreography was stunning. Chills.",
    "Late red card changed everything.",
    "Player made his 100th appearance. Legend.",
    "Weather delayed the start by 20 minutes.",
    "Final ball was always just behind the striker.",
    "So close to a comeback. One more minute.",
    "Team looked comfortable throughout.",
    "Keeper saved a penalty with his foot!",
    "Defensive mix-up led to the goal.",
    "Player was subbed off in tears. Hope he’s okay.",
    "We’ve got depth now. Bench made a difference.",
    "Tactical foul in the 94th minute saved the point.",
    "Player showed great sportsmanship after the whistle.",
    "Long ball found the striker perfectly.",
    "Team needs to be more clinical.",
    "Scoreline flattered us. Lucky to win.",
    "Supporters stayed until the end. Respect.",
    "First goal came from a defensive error.",
    "Player’s movement off the ball was intelligent.",
    "Missed a penalty shootout. Tough way to lose.",
    "Youngster started for the first time. Nailed it.",
    "Team showed character to equalize.",
    "Opposition had the better chances.",
    "Keeper’s reaction save in the 78th minute was insane.",
    "Final pass was always a yard too heavy.",
    "So proud of the progress this season.",
    "Tactical switch at halftime changed the game.",
    "Player received a guard of honor. Emotional.",
    "Crosses were all too high.",
    "Team played with passion and pride.",
    "Need to work on transitions.",
    "Last-minute winner! Unbelievable scenes!",
    "Player was stretchered off. Hope it’s not bad.",
    "Fans sang his name the whole match. Icon.",
    "Team looked flat from the start.",
    "Perfectly executed set piece goal.",
    "Substitute keeper made his debut. Clean sheet!",
    "Midfield was overrun in the first half.",
    "Player scored and pointed to the sky. Beautiful.",
    "So disappointed with the officiating.",
    "Team adapted quickly to the rain.",
    "Final third decision-making needs work.",
    "Captain’s leadership was vital tonight.",
    "Player made a mistake but got redemption with a goal.",
    "Long-range strike caught the keeper off guard.",
    "Team needs more consistency.",
    "Backheel pass in the final third was magical.",
    "Keeper came off his line perfectly.",
    "So happy for the fans. They deserved this.",
    "Player was booked for a late challenge.",
    "Team showed resilience under pressure.",
    "Missed chance in the 90th minute cost us.",
    "Final whistle brought tears of joy.",
    "Player got a standing ovation at the substitution.",
    "Tactical discipline was excellent.",
    "Team played with heart and soul.",
    "Need to protect the ball better in the final third.",
    "Scored from a free kick with the outside of the boot!",
    "Fan’s banner said ‘We’ll follow you anywhere’ — so true.",
    "Player’s return from injury was seamless.",
    "Team looked sharp in training this week.",
    "Late tackle earned a yellow. Deserved.",
    "Backpass was too short, led to a goal.",
    "So proud of the academy product stepping up.",
    "Team needs to build on this performance.",
    "Player’s work rate was off the charts.",
    "Final corner came to nothing. Frustrating.",
    "Keeper punched it clear under pressure.",
    "Team played with more aggression.",
    "Substitute changed the game. Manager’s call.",
    "Player received a red card. Harsh but correct.",
    "Team showed maturity in victory.",
    "Missed a header from two yards out. How?",
    "Final ball was always intercepted.",
    "So happy to see clean sheets becoming regular.",
    "Player celebrated with a unique dance. Fun!",
    "Team needs to improve set-piece defending.",
    "Long ball found the winger in space.",
    "Backheel flick set up the goal. Genius.",
    "Keeper saved it with his legs!",
    "Team played with confidence and flair.",
    "Player apologized to teammates after mistake.",
    "Final whistle brought a sense of relief.",
    "Tactical formation maximized our strengths.",
    "Team showed unity in defeat.",
    "Need to reduce individual errors.",
    "Scored from a counter-attack. Speed was key.",
    "Fan chants were loud and proud.",
    "Player made his debut. Solid performance.",
    "Team looked tired in extra time.",
    "Late run into the box created the winner.",
    "Backpass was perfect. No pressure.",
    "So proud of the fight. Never gave up.",
    "Player was stretchered off. Everyone’s praying.",
    "Team needs to be more clinical in front of goal.",
    "Final touch lacked composure.",
    "Keeper palmed it around the post. Huge save.",
    "Team played with intensity from start to finish.",
    "Substitute scored on his first touch!",
    "Player received a yellow for dissent.",
    "Team showed character to come back.",
    "Missed a penalty. Tough to watch.",
    "Final whistle brought joy and relief.",
    "Player lifted the trophy with pride.",
    "Team played with passion and purpose.",
    "Need to work on defensive transitions.",
    "Scored from a rebound. Took the chance.",
    "Fan support was incredible. Felt it on the pitch.",
    "Player returned after injury. Made an impact.",
    "Team looked organized and compact.",
    "Late tackle stopped a breakaway. Deserved yellow.",
    "Backheel pass split the defense!",
        "That goal was an absolute banger! Top bins.",
    "We’ve been so mid this season, but tonight felt different.",
    "Keeper pulled off some sick saves. Proper hero.",
    "Our defense was shaky early on but cleaned up later.",
    "Lowkey think he’s the most underrated player in the league.",
    "What a waste of a chance. Should’ve buried that.",
    "The vibe in the stadium was immaculate!",
    "He’s been quiet lately, but tonight he came alive.",
    "Bare proud of how the boys turned it around.",
    "That tackle was straight fire. Perfect timing.",
    "Honestly, the ref had a poor game. Missed too much.",
    "First half was a bit of a snooze, but second half? Fire.",
    "Sub came on and changed the game — proper impact.",
    "They kept it tight and took their chance. Solid win.",
    "Not the prettiest game, but we got the job done."
]  # Define 300 comments
headers = {  # Update headers
    'Content-Type': 'application/json',  # Set JSON type
    'X-CSRFToken': csrf_token  # Set CSRF token
}

results = []  # Initialize results
for i, comment in enumerate(comments, 1):  # Loop comments
    data = {'comment': comment, 'topic_id': 1}  # Prepare data
    response = session.post(sentiment_url, headers=headers, data=json.dumps(data))  # Post comment
    if response.status_code == 200:  # Check response
        result = response.json()  # Parse JSON
        sentiment = result['sentiment']  # Get sentiment
        results.append((comment, sentiment))  # Store result
        print(f"Comment {i}: '{comment}' -> Sentiment: {sentiment}")  # Print result
    else:
        print(f"Error on Comment {i}: {response.status_code} - {response.text}")  # Print error

# Step 4: Save results for analysis
with open('sentiment_results.txt', 'w') as f:  # Open file
    for i, (comment, sentiment) in enumerate(results, 1):  # Loop results
        f.write(f"Comment {i}: '{comment}' -> Sentiment: {sentiment}\n")  # Write result
print("Results saved to sentiment_results.txt")  # Print completion