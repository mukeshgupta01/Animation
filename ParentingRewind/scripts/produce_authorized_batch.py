"""Resumable local-only producer for the authorized Parenting Rewind batch.

It creates versioned MP4s, SRT captions, research metadata and quality reports.
It contains no uploader, OAuth logic, email integration or Scheduled Task code.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import edge_tts
from PIL import Image


PROJECT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT / "output"
WORK_ROOT = PROJECT / "production-work" / "authorized-batch-2026-08-23"
METADATA = PROJECT / "metadata"
MUSIC = PROJECT / "production-work" / "pilot-02-screen-time-v1" / "original-dynamic-emotional-score.wav"
W, H, FPS = 1080, 1920, 30
VOICE = "en-US-AvaMultilingualNeural"

ASSETS = {
    "entryway": PROJECT / "production-assets" / "pilot-01-shoe-storyboard.png",
    "living-room": PROJECT / "production-assets" / "screen-time-storyboard-01.png",
    "supermarket": PROJECT / "production-assets" / "supermarket-storyboard-01.png",
}

SOURCES = {
    "directions": {
        "organization": "Centers for Disease Control and Prevention",
        "title": "Steps for Giving Good Directions",
        "url": "https://www.cdc.gov/parenting-toddlers/directions/good-directions.html",
    },
    "rules": {
        "organization": "Centers for Disease Control and Prevention",
        "title": "Tips for Creating Rules",
        "url": "https://www.cdc.gov/parenting-toddlers/structure-rules/rules.html",
    },
    "praise": {
        "organization": "Centers for Disease Control and Prevention",
        "title": "Tips for Praise, Imitation, and Description",
        "url": "https://www.cdc.gov/parenting-toddlers/communication/praise.html",
    },
    "consequences": {
        "organization": "Centers for Disease Control and Prevention",
        "title": "Tips for Using Consequences",
        "url": "https://www.cdc.gov/parenting-toddlers/discipline-consequences/consequences.html",
    },
    "play": {
        "organization": "Centers for Disease Control and Prevention",
        "title": "Tips for Child-led Play",
        "url": "https://www.cdc.gov/parenting-toddlers/communication/special-playtime.html",
    },
    "sleep": {
        "organization": "American Academy of Pediatrics / HealthyChildren.org",
        "title": "Toddler Bedtime Trouble: 7 Tips for Parents",
        "url": "https://www.healthychildren.org/English/healthy-living/sleep/Pages/bedtime-trouble.aspx",
    },
    "food": {
        "organization": "American Academy of Pediatrics / HealthyChildren.org",
        "title": "10 Tips for Parents of Picky Eaters",
        "url": "https://www.healthychildren.org/English/ages-stages/toddler/nutrition/Pages/Picky-Eaters.aspx",
    },
    "siblings": {
        "organization": "American Academy of Pediatrics / HealthyChildren.org",
        "title": "Sibling Relationships: How to Help Your Kids Build Healthy Bonds",
        "url": "https://www.healthychildren.org/English/family-life/family-dynamics/Pages/Sibling-Synergy.aspx",
    },
    "screen": {
        "organization": "American Academy of Pediatrics / HealthyChildren.org",
        "title": "Screen Time & Temper Tantrums: Helpful Tips for Parents",
        "url": "https://www.healthychildren.org/English/family-life/Media/Pages/screen-time-and-temper-tantrums-helpful-tips-for-parents.aspx",
    },
}

# slug, title, hook, unhelpful reaction, calmer response, takeaway, asset, source
EPISODES = [
    ("supermarket-snack", "When They Demand a Supermarket Snack", "Your five-year-old spots a snack and treats no like an emergency.", "A rushed no, followed by a lecture about sugar, adds attention without making the limit clearer.", "Pause, get close, and say: We are not buying that today; you may choose apples or bananas for the trolley.", "Acknowledge disappointment, offer only choices you can accept, and keep shopping without reopening the decision.", "supermarket", "directions"),
    ("checkout-waiting", "The Checkout Line Without Constant Warnings", "Waiting at checkout can feel endless to a young child and exhausting to you.", "Repeating stop it every few seconds gives no clear picture of what to do.", "Before joining the line, say: Stay beside the trolley and help me find three blue things; then notice the first moment they do it.", "A short direction plus specific positive attention is more useful than a stream of vague corrections.", "supermarket", "praise"),
    ("leaving-playground", "Leaving the Playground Without a Chase", "The hardest part of playground time is sometimes the last two minutes.", "Calling from far away and adding five more warnings teaches that the first warning does not matter.", "Move close, give one clear transition, and say: One last slide, then hold my hand to the gate.", "Make the ending predictable, keep the direction concrete, and follow through calmly when the final turn is done.", "supermarket", "directions"),
    ("public-meltdown", "When a Public Meltdown Draws an Audience", "Your child is crying on the floor and suddenly every stranger seems to be watching.", "Arguing your case or threatening a huge punishment can turn embarrassment into escalation.", "Lower your voice, move to safety, and use few words: You are upset; I am here; the answer is still no.", "The audience is not the priority; safety, a steady limit, and reconnection after the storm are.", "supermarket", "consequences"),
    ("shopping-helper", "Turn Grocery Shopping Into Cooperation", "A bored six-year-old can find trouble in every supermarket aisle.", "Correcting every touch keeps both of you focused on what is going wrong.", "Give a real job before problems start: Please find the oats and place them gently in the trolley.", "One age-fitting responsibility and specific praise can create more cooperation than constant policing.", "supermarket", "praise"),
    ("morning-coat", "When They Refuse a Coat", "You are late, it is cold, and your child suddenly hates every coat they own.", "Debating whether they should feel cold pulls you into a power struggle about their body.", "State the boundary and offer two workable options: The coat comes with us; wear it now or carry it to the car.", "Keep health and safety limits firm while leaving a small piece of control with the child.", "entryway", "directions"),
    ("school-bag", "The School Bag Is Still on the Floor", "You have asked about the school bag four times and nobody is moving.", "A long list about shoes, lunch, teeth, and the bag can overwhelm a child who has not started step one.", "Get attention and give one direction: Put your lunchbox in the bag; then wait and praise completion before the next step.", "One direction at a time makes success easier to see and easier to reinforce.", "entryway", "directions"),
    ("slow-morning", "A Slow Morning Without Shouting", "Some children move at dream speed exactly when the clock moves fastest.", "Saying hurry up louder does not explain the next action.", "Point to the routine and say: Socks first; when they are on, come show me.", "Replace urgency words with one observable step, then notice progress instead of waiting only for perfection.", "entryway", "directions"),
    ("wrong-shoes", "When Only the Wrong Shoes Will Do", "Your preschooler wants sandals on a rainy morning and rejects the practical pair.", "Insisting that your choice is obviously better invites an argument about taste.", "Hold the weather boundary and offer two acceptable pairs: Red boots or blue boots; you choose.", "A bounded choice is not giving in; it is sharing control inside a limit you have already set.", "entryway", "rules"),
    ("doorway-stall", "The Doorway Stall at the Worst Moment", "Just as you open the door, your child remembers one more toy, drink, and story.", "Answering every new request can accidentally turn delay into a successful strategy.", "Name the plan once: We are leaving now; choose one small toy before I count to ten, or we leave without one.", "Make the transition clear, keep the consequence related, and reconnect once everyone is moving.", "entryway", "consequences"),
    ("toy-cleanup", "Toy Cleanup Without Saying It Ten Times", "The floor is covered in toys and your child seems unable to hear the word cleanup.", "Pick up everything now is broad enough to feel impossible.", "Start beside them and give one concrete step: Put the blocks in this basket; then specifically praise that action.", "Small directions build momentum, and labeled praise tells the child exactly what cooperation looked like.", "living-room", "directions"),
    ("interrupting", "When Your Child Interrupts Every Sentence", "You begin an adult conversation and your child suddenly needs twenty things.", "Snapping stop interrupting names the problem but not the replacement behavior.", "Teach the signal outside the heated moment: Put your hand on my arm, and I will place my hand over yours to show I noticed.", "A simple family rule works best when it states what to do, is practiced, and is praised when used.", "living-room", "rules"),
    ("whining", "Responding to Whining Without Whining Back", "A simple request arrives in the voice that makes your shoulders tighten.", "Copying the tone or delivering a speech gives the whining a large emotional payoff.", "Keep your face and voice neutral: I will listen when you use your regular voice; then respond warmly to the first calmer attempt.", "Give less attention to minor whining and more immediate attention to the behavior you want repeated.", "living-room", "consequences"),
    ("hitting", "When One Child Hits Another", "One child hits and both children look to you for what happens next.", "Demanding an instant apology before anyone is calm can produce words without safety or learning.", "Block the hit, separate if needed, and say: I will not let you hit; hands stay safe; we will talk when bodies are calmer.", "Safety comes first, followed by a clear rule, a related response, and repair when the child can participate.", "living-room", "rules"),
    ("sharing-toy", "They Both Want the Same Toy", "Two children, one toy, and neither is interested in a lecture about sharing.", "Forcing the child who had it first to surrender immediately can make sharing feel like losing.", "Protect the current turn and make the next turn predictable: She is using it; you are next when the timer rings.", "Turn-taking is concrete; stay neutral, prevent grabbing, and help both children trust the sequence.", "living-room", "siblings"),
    ("sibling-fight", "Stop Refereeing Every Sibling Fight", "You hear shouting and rush in ready to decide who started it.", "Choosing a villain before listening can intensify competition for your approval.", "Check safety, separate for a pause if needed, then hear each child briefly and restate the shared rule.", "Be a calm boundary keeper, not a courtroom; older children can help propose a workable next step.", "living-room", "siblings"),
    ("losing-game", "When Losing a Game Ends in Tears", "The game was fun until somebody else won.", "Calling the reaction silly adds shame to disappointment.", "Name the feeling and hold the rule: You wanted to win; it is okay to be upset, and the pieces stay on the table.", "Children can learn to lose without liking it; model calm, protect the game, and praise recovery.", "living-room", "rules"),
    ("toy-throwing", "When a Toy Becomes a Projectile", "The toy flies across the room after one frustrated moment.", "Threatening to remove every toy for a month is hard to follow and unrelated to what happened.", "Use an immediate logical response: Trucks are for rolling; if you throw it again, this truck rests until tomorrow.", "Warnings work when they are specific, reasonable, and followed by exactly the consequence you named.", "living-room", "consequences"),
    ("bedtime-start", "Start Bedtime Before Everyone Is Exhausted", "Bedtime resistance often begins before anyone reaches the bedroom.", "Waiting until a child is overtired and then rushing every step makes cooperation harder.", "Use the same calm sequence each night: bathroom, pajamas, book, bed, with a brief warning before it begins.", "A predictable routine reduces surprises; consistency matters more than creating a perfect night.", "living-room", "sleep"),
    ("toothbrushing", "Toothbrushing Without a Wrestling Match", "The toothbrush appears and your child clamps their mouth shut.", "Chasing them with the brush turns a health routine into a game of escape.", "Keep the boundary and offer participation: You brush first or I brush first; then we finish together.", "Use a small choice inside the non-negotiable routine and keep your tone matter-of-fact.", "living-room", "directions"),
    ("bath-exit", "Getting Out of the Bath", "The bath was impossible to start and is now impossible to end.", "Draining the water without warning can make a difficult transition feel abrupt.", "Give one clear ending cue: Two more pours, then towel; let the child complete the final pour.", "Predictable endings and limited choices can support transitions without changing the boundary.", "living-room", "directions"),
    ("pajamas", "When Pajamas Become the Battle", "Your child rejects pajamas because every seam suddenly feels wrong.", "Arguing that the fabric is fine dismisses the experience and keeps the conflict alive.", "Pause, check for a practical discomfort, then offer two comfortable sets that meet the bedtime plan.", "Solve what is solvable, keep the routine moving, and seek professional advice if sensory distress is frequent or severe.", "living-room", "sleep"),
    ("one-more-story", "The One-More-Story Loop", "You finish the bedtime book and immediately hear: one more.", "Saying yes repeatedly teaches that the routine ends only after enough persistence.", "Set the limit before reading: Tonight we choose two books; after the second, it is cuddle and lights out.", "Warmth and limits can coexist; make the ending known early and follow the same sequence.", "living-room", "sleep"),
    ("night-worry", "When Worries Arrive at Lights-Out", "The room gets quiet and every worry from the day suddenly gets loud.", "Promising that nothing bad can ever happen may end the conversation without helping the child feel understood.", "Listen briefly, name the worry, and return to a familiar calming routine such as one slow breath and one safe thought.", "Offer connection without turning bedtime into an endless problem-solving session; persistent worries deserve professional support.", "living-room", "sleep"),
    ("picky-dinner", "Dinner Is Not a Bite Negotiation", "You cooked dinner and your child announces they hate it before looking.", "Counting bites or threatening dessert turns appetite into a contest.", "Serve a balanced meal with at least one familiar food, let the child choose what and how much to eat, and stay neutral.", "The adult provides the meal structure; the child listens to hunger and chooses from what is offered.", "living-room", "food"),
    ("new-food", "Helping a New Food Feel Less Scary", "A new food lands on the plate and is rejected on sight.", "Requiring a big bite can make exploration feel unsafe.", "Offer a tiny portion beside familiar food and allow steps such as touching, smelling, or tasting without pressure.", "Repeated low-pressure exposure is practice, not a test; one refusal does not predict the future.", "living-room", "food"),
    ("dessert-bribe", "Why Dessert Bribes Backfire", "You hear yourself say: three bites of vegetables and then you get dessert.", "The bargain makes dessert the prize and vegetables the unpleasant price.", "Offer the planned meal without negotiating bites, and keep dessert decisions separate from whether a child cleans the plate.", "Remove the food hierarchy from the argument and focus on regular meals, variety, and calm modeling.", "living-room", "food"),
    ("leaving-table", "When They Keep Leaving the Table", "Your preschooler takes one bite, runs away, and returns five minutes later.", "Following them with a fork makes movement the center of the meal.", "State a simple routine: Food stays at the table; you may sit with us or tell me when you are finished.", "Keep meal boundaries predictable and age-appropriate while avoiding pressure about how much must be eaten.", "living-room", "rules"),
    ("meal-device", "The Tablet at Dinner", "Turning off the dinner tablet feels harder than serving the meal.", "Removing it mid-show without a plan invites an abrupt transition.", "Set the rule before the meal: Screens park on the counter at dinner; give a warning and model parking your own phone too.", "Family rules are easier to follow when adults model them and all caregivers use the same expectation.", "living-room", "screen"),
    ("spilled-drink", "A Spilled Drink Is a Teaching Moment", "The cup tips and your first thought is: I told you to be careful.", "A lecture cannot put the drink back and may make mistakes feel dangerous to admit.", "Pause and say: Spills happen; get the towel and I will move the plate; then help with a manageable cleanup step.", "Natural repair teaches responsibility better than shame: notice the problem, help fix it, and move on.", "living-room", "consequences"),
    ("admit-mistake", "Help Them Admit a Mistake", "You know what happened, but your child is afraid to tell you.", "Leading with anger can make self-protection feel safer than honesty.", "Regulate first and say: I care about the truth; tell me what happened, and then we will work out how to repair it.", "Make honesty emotionally possible while still keeping a clear, related consequence for the behavior.", "living-room", "consequences"),
    ("lying", "When Your Child Tells an Obvious Lie", "The marker is in their hand, but they insist the wall drew on itself.", "Calling them a liar turns one behavior into an identity.", "Describe what you see and invite a reset: The marker is here and the wall is drawn on; try the true answer, then help me clean it.", "Focus on truth and repair, not labels; calm consequences make honesty easier next time.", "living-room", "consequences"),
    ("apology", "Do Not Force a Fast Apology", "After a conflict, adults often want the word sorry immediately.", "A forced apology can become a password that ends the consequence without repairing anything.", "Wait for calm, then ask: What happened, who was affected, and what can you do to help make it better?", "Repair may include words, returning an item, rebuilding, or giving space; sincerity grows from understanding impact.", "living-room", "siblings"),
    ("rude-tone", "When the Tone Is Rude but the Need Is Real", "Your child needs help but asks in a way that instantly irritates you.", "Refusing to hear the need until they sound cheerful can create a second conflict.", "Keep the boundary simple: I can help; try that again respectfully, then offer the exact words if they are stuck.", "Teach the replacement language and respond when it appears, even if the child is still disappointed.", "living-room", "directions"),
    ("copied-swear", "When a Young Child Copies a Swear Word", "A surprising word comes from a small mouth and everyone freezes.", "A huge shocked reaction can make the word fascinating and powerful.", "Stay neutral, state the family rule, and give a replacement: We do not use that word at people; say I am really mad.", "Keep the response brief, model the language you want, and notice appropriate expression later.", "living-room", "rules"),
    ("public-manners", "Teaching Manners Without Public Shame", "Your child forgets to say thank you and another adult is waiting.", "Correcting them harshly in front of everyone can turn manners into humiliation.", "Model the words calmly: Thank you for the gift; then practice the expected response privately later.", "Manners are learned through repetition and modeling, not proof that a child is good or bad.", "supermarket", "praise"),
    ("car-seat", "When They Refuse the Car Seat", "The trip cannot begin safely until the buckle is done.", "Negotiating whether the restraint is necessary makes a safety limit sound optional.", "Use few words and a small choice: The buckle must close; climb in yourself or I will help your body in.", "Safety boundaries stay firm; reduce debate, offer limited control, and follow current restraint guidance.", "entryway", "directions"),
    ("parking-lot", "The Parking Lot Hand-Holding Rule", "Your child wants independence exactly where cars are moving.", "Shouting be careful is vague and arrives after the danger has started.", "Before stepping out, state the observable rule: In the car park, hold my hand or keep one hand on the trolley.", "Safety rules should be short, practiced, consistent, and paired with immediate follow-through.", "supermarket", "rules"),
    ("helmet", "When the Helmet Is Non-Negotiable", "The bike is ready, but your child says the helmet ruins everything.", "Threatening to throw the bike away turns one safety step into a bigger battle.", "State the linked consequence: Wheels move only after the helmet is fastened; you may buckle it or ask for help.", "A logical consequence is immediate and related: no safe gear means the riding activity waits.", "entryway", "consequences"),
    ("doctor-visit", "Prepare for a Difficult Appointment", "A child who fears the doctor may resist before you even leave home.", "Saying it will not hurt can damage trust if something is uncomfortable.", "Explain simply what will happen, allow honest questions, and offer a coping choice such as lap or chair when available.", "Predictability and truthful reassurance help more than promises you cannot guarantee; ask clinicians for individualized guidance.", "entryway", "directions"),
    ("school-dropoff", "A Calmer School Drop-Off", "Your child clings at the classroom door and your own worry rises too.", "Sneaking away may avoid tears now but can weaken trust in the goodbye.", "Use a short repeatable ritual: one hug, one clear return time, and a confident handoff to the trusted adult.", "Keep goodbyes warm and predictable; seek support from the school if distress is intense or persistent.", "entryway", "rules"),
    ("new-teacher", "When a New Teacher Feels Scary", "A new classroom can make even a capable child suddenly unsure.", "Pushing them to be brave dismisses the uncertainty they are trying to share.", "Name the feeling and make the next step concrete: New can feel strange; first we find your hook, then we greet your teacher.", "Confidence grows through supported action, not pressure to stop feeling nervous.", "entryway", "directions"),
    ("homework-start", "Starting Homework Without a Daily Fight", "The worksheet is small, but beginning it feels enormous after school.", "A lecture about responsibility adds more language when the child needs a starting point.", "Build a predictable reset, then give one step: Snack, ten minutes of movement, then write your name and do question one.", "Routines reduce negotiation; start small, notice effort, and adjust expectations to the child's age and school needs.", "living-room", "directions"),
    ("perfectionism", "When Mistakes Feel Unbearable", "One crooked letter makes your child want to tear up the whole page.", "Saying it is easy can make their struggle feel invisible.", "Reflect the frustration and model a repair: You wanted it exact; circle the part to retry, and keep the rest of your work.", "Praise persistence and strategy rather than demanding flawless results; recurring severe distress deserves professional support.", "living-room", "praise"),
    ("task-frustration", "Before You Rescue Them From Frustration", "Your child struggles with a puzzle and immediately hands it to you.", "Finishing it for them removes the discomfort but also the chance to practice.", "Stay nearby and offer the smallest useful prompt: Turn one piece and check the corners; then let them take the next action.", "Support is not the same as taking over; describe effort and let the child own the success.", "living-room", "praise"),
    ("chores", "Make Chores Clear Enough to Do", "Clean your room can mean twenty different jobs to a six-year-old.", "Calling the child lazy when they stall confuses a missing skill with a character flaw.", "Choose one visible task: Put dirty clothes in the basket; when that is done, give the next direction.", "Break responsibility into teachable steps and use specific praise while the routine is still new.", "living-room", "directions"),
    ("sibling-privacy", "Teach Siblings to Respect Privacy", "One child walks into the other's room and the argument starts instantly.", "Telling the older child to just share their space ignores a reasonable boundary.", "Create a family rule everyone can follow: Knock, wait for an answer, and ask before borrowing.", "Clear privacy rules reduce resentment when adults apply them consistently across children.", "living-room", "siblings"),
    ("grabbing", "When a Preschooler Grabs", "Your child sees a toy and takes it before the other child can react.", "A public demand to share nicely is too vague to guide the next move.", "Return the toy, state the rule, and coach the phrase: Ask, can I have a turn when you are done?", "Young children need the replacement action repeated many times; praise the first attempt to ask or wait.", "living-room", "rules"),
    ("screen-warning", "Make Screen Endings Predictable", "The episode ends, but your child insists the screen cannot possibly stop there.", "An abrupt grab creates a new conflict on top of the disappointment.", "Give the ending before play begins, use a timer or natural stopping point, and say what comes next.", "Warnings are tools, not guarantees; acknowledge the protest, hold the limit, and follow through without a lecture.", "living-room", "screen"),
    ("autoplay", "Autoplay Is Not a Parenting Plan", "One video quietly becomes five while everyone loses track of the agreement.", "Blaming the child for not stopping ignores a feature designed to keep content moving.", "Turn autoplay off when possible and decide the stopping point before the screen starts.", "Change the environment as well as the conversation; predictable limits are easier when the device supports them.", "living-room", "screen"),
    ("parent-phone", "When Your Phone Keeps Interrupting Connection", "Your child asks you to watch, but your eyes keep returning to notifications.", "Saying just a second repeatedly can leave the child competing with a device that always wins.", "Put the phone out of reach for a short, named window and say: I have ten minutes just for your game.", "Brief focused attention can be more connecting than a longer stretch of half-attention.", "living-room", "play"),
    ("child-led-play", "Ten Minutes of Child-Led Play", "Playtime can become another place where adults give directions and corrections.", "Taking over the build or asking constant questions shifts the lead back to you.", "Let the child choose a safe activity, then imitate, describe, and specifically praise what they are doing.", "A predictable short playtime can strengthen connection when the child leads and the adult pays warm attention.", "living-room", "play"),
    ("specific-praise", "Replace Good Job With What You Noticed", "Good job is kind, but it can leave a child guessing what worked.", "Saving attention only for perfect behavior misses the small steps that build it.", "Name the action: You put the blocks in the basket when I asked; that was helpful.", "Specific praise makes the desired behavior visible and is most useful soon after it happens.", "living-room", "praise"),
    ("repair-after-yelling", "Repair After You Lose Your Temper", "Sometimes the rewind is for the parent, because you already shouted.", "Pretending it did not happen teaches that power removes the need to repair.", "Return when calm and say: I yelled; that was not okay; the limit still stands, and I will try again without shouting.", "An apology does not erase the boundary; it models responsibility, reconnects, and names what you will do differently.", "living-room", "praise"),
]

BEAT_LABELS = ["THE MOMENT", "THE TRAP", "PAUSE", "SAY THIS INSTEAD", "THE TAKEAWAY"]


def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def media_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True).strip())


def stamp(seconds: float, ass: bool = False) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole, milliseconds = divmod(milliseconds, 1000)
    if ass:
        return f"{hours}:{minutes:02d}:{whole:02d}.{milliseconds // 10:02d}"
    return f"{hours:02d}:{minutes:02d}:{whole:02d},{milliseconds:03d}"


def split_panels(asset_key: str) -> list[Path]:
    target_dir = WORK_ROOT / "shared-panels" / asset_key
    targets = [target_dir / f"panel-{index}.jpg" for index in range(6)]
    if all(path.exists() for path in targets):
        return targets
    target_dir.mkdir(parents=True, exist_ok=True)
    source = Image.open(ASSETS[asset_key]).convert("RGB")
    margin = 7
    for index, target in enumerate(targets):
        row, col = divmod(index, 3)
        x1 = round(col * source.width / 3) + margin
        x2 = round((col + 1) * source.width / 3) - margin
        y1 = round(row * source.height / 2) + margin
        y2 = round((row + 1) * source.height / 2) - margin
        source.crop((x1, y1, x2, y2)).save(target, quality=94)
    return targets


async def create_voice(text: str, audio: Path, boundaries: Path) -> None:
    if audio.exists() and boundaries.exists():
        return
    if audio.exists() != boundaries.exists():
        raise RuntimeError(f"Incomplete narration pair: {audio}, {boundaries}")
    await edge_tts.Communicate(text, VOICE, rate="-5%", pitch="-1Hz", volume="-1%").save(
        str(audio), str(boundaries)
    )


def word_boundaries(path: Path, voice_start: float, voice_end: float) -> list[dict]:
    items = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    words = [item for item in items if item.get("type") == "WordBoundary"]
    if not words:
        sentences = [item for item in items if item.get("type") == "SentenceBoundary"]
        if not sentences:
            raise RuntimeError("Speech service returned no usable boundaries")
        result = []
        for sentence in sentences:
            tokens = str(sentence["text"]).split()
            groups = [tokens[i:i + 8] for i in range(0, len(tokens), 8)]
            sentence_start = voice_start + float(sentence["offset"]) / 10_000_000
            sentence_duration = float(sentence["duration"]) / 10_000_000
            weights = [max(1, sum(len(token) + 1 for token in group)) for group in groups]
            total_weight = sum(weights)
            cursor = sentence_start
            for group, weight in zip(groups, weights):
                duration = sentence_duration * weight / total_weight
                result.append({"start": cursor, "end": min(voice_end, cursor + duration - 0.03), "text": " ".join(group)})
                cursor += duration
        return result
    cues, group = [], []
    for item in words:
        group.append(item)
        length = sum(len(str(part["text"])) + 1 for part in group)
        if len(group) >= 8 or length >= 48:
            cues.append(group)
            group = []
    if group:
        cues.append(group)
    result = []
    for index, cue in enumerate(cues):
        first, last = cue[0], cue[-1]
        start = voice_start + float(first["offset"]) / 10_000_000
        natural_end = voice_start + (float(last["offset"]) + float(last["duration"])) / 10_000_000
        if index + 1 < len(cues):
            next_start = voice_start + float(cues[index + 1][0]["offset"]) / 10_000_000
            end = max(natural_end, next_start - 0.03)
        else:
            end = min(voice_end, natural_end + 0.12)
        result.append({"start": start, "end": end, "text": " ".join(str(part["text"]) for part in cue)})
    return result


def write_srt(cues: list[dict], target: Path) -> None:
    blocks = [f"{i}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i, c in enumerate(cues, 1)]
    target.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def write_ass(title: str, total: float, cues: list[dict], target: Path) -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Brand,Segoe UI,28,&H00FFFFFF,&H00FFFFFF,&H50000000,&HC8000000,-1,0,0,0,100,100,1,0,3,1,0,8,54,54,60,1
Style: Title,Segoe UI Semibold,48,&H00FFFFFF,&H00FFFFFF,&H60000000,&HD0000000,-1,0,0,0,100,100,0,0,3,2,0,8,60,60,125,1
Style: Beat,Segoe UI Semibold,34,&H004BBcf4,&H004BBcf4,&H50000000,&HB8000000,-1,0,0,0,100,100,1,0,3,1,0,8,80,80,275,1
Style: Caption,Segoe UI Semibold,52,&H00FFFFFF,&H00FFFFFF,&H70000000,&HDC15120E,-1,0,0,0,100,100,0,0,3,2,0,2,70,70,210,1
Style: Footer,Segoe UI,20,&H00E8E8E8,&H00FFFFFF,&H50000000,&H90000000,0,0,0,0,100,100,0,0,3,1,0,2,60,60,42,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header.rstrip()]
    lines.append(f"Dialogue: 0,{stamp(0, True)},{stamp(total, True)},Brand,,0,0,0,,PARENTING REWIND")
    lines.append(f"Dialogue: 0,{stamp(0, True)},{stamp(total, True)},Title,,0,0,0,,{ass_escape(title.upper())}")
    beat_length = total / len(BEAT_LABELS)
    for index, beat in enumerate(BEAT_LABELS):
        lines.append(f"Dialogue: 0,{stamp(index * beat_length, True)},{stamp((index + 1) * beat_length, True)},Beat,,0,0,0,,{beat}")
    for cue in cues:
        lines.append(f"Dialogue: 0,{stamp(cue['start'], True)},{stamp(cue['end'], True)},Caption,,0,0,0,,{ass_escape(cue['text'])}")
    lines.append(f"Dialogue: 0,{stamp(0, True)},{stamp(total, True)},Footer,,0,0,0,,GENERAL PARENTING EDUCATION  •  EVERY CHILD IS DIFFERENT")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def panel_order(index: int) -> list[int]:
    orders = ([0,1,2,3,4,5], [0,2,1,3,5,4], [1,0,2,4,3,5], [0,1,3,2,4,5], [1,2,0,3,4,5], [0,2,3,1,4,5])
    return list(orders[index % len(orders)])


def render_video(panels: list[Path], order: list[int], total: float, voice: Path, ass: Path, output: Path, work: Path) -> None:
    still = max(1.0, total / 6)
    inputs: list[str] = []
    for panel_index in order:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{still:.3f}", "-i", str(panels[panel_index])]
    inputs += ["-i", str(voice), "-stream_loop", "-1", "-i", str(MUSIC)]
    filters = []
    for i in range(6):
        x = "(iw-ow)*0.44" if i % 2 == 0 else "(iw-ow)*0.56"
        filters.append(
            f"[{i}:v]scale=1200:2100:force_original_aspect_ratio=increase,crop=1080:1920:x='{x}':y='(ih-oh)/2',"
            f"eq=saturation=0.96:brightness=-0.015,fade=t=in:st=0:d=0.22,fade=t=out:st={max(0, still-.22):.3f}:d=0.22,setsar=1[v{i}]"
        )
    filters.append("".join(f"[v{i}]" for i in range(6)) + "concat=n=6:v=1:a=0[base]")
    filters.append("[base]ass=overlay.ass[v]")
    filters.append("[6:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.16,asplit=2[voice_side][voice_mix]")
    filters.append(f"[7:a]atrim=duration={total:.3f},aformat=sample_rates=48000:channel_layouts=stereo,volume=3.0[music]")
    filters.append("[music][voice_side]sidechaincompress=threshold=.025:ratio=3.2:attack=18:release=320[ducked]")
    filters.append("[ducked][voice_mix]amix=inputs=2:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=9[a]")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(output)], cwd=work)


def validate(output: Path, total: float, srt: Path, meta: Path, work: Path) -> dict:
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-show_entries", "stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json", str(output)
    ], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    checks = {
        "nontrivial_size": output.stat().st_size > 1_000_000,
        "duration_matches": abs(float(probe["format"]["duration"]) - total) < 0.4,
        "vertical_h264_1080x1920": video.get("codec_name") == "h264" and video.get("width") == W and video.get("height") == H,
        "aac_48khz_stereo": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
        "caption_sidecar": srt.exists() and srt.stat().st_size > 100,
        "metadata_exists": meta.exists() and meta.stat().st_size > 500,
    }
    report = {"output": str(output), "duration_seconds": float(probe["format"]["duration"]), "size_bytes": int(probe["format"]["size"]), "checks": checks, "passed": all(checks.values())}
    (work / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["passed"]:
        raise RuntimeError(f"Quality gate failed: {report}")
    return report


async def produce(index: int, spec: tuple) -> dict:
    slug, title, hook, wrong, better, takeaway, asset_key, source_key = spec
    episode_number = index + 3
    episode_id = f"parenting-rewind-{episode_number:03d}-{slug}"
    output = OUTPUT / f"{episode_id}-v1.mp4"
    work = WORK_ROOT / episode_id
    meta_path = METADATA / f"{episode_id}-v1.json"
    quality_path = work / "quality-report.json"
    if output.exists() and quality_path.exists() and json.loads(quality_path.read_text(encoding="utf-8")).get("passed"):
        return {"episode": episode_id, "status": "preserved-existing", "output": str(output)}
    work.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    METADATA.mkdir(parents=True, exist_ok=True)
    pause = "Before reacting, pause for one breath so the next words can be short, clear, and useful."
    narration = " ".join((hook, wrong, pause, better, takeaway))
    voice = work / "narration.mp3"
    boundaries = work / "narration-boundaries.jsonl"
    await create_voice(narration, voice, boundaries)
    voice_duration = media_duration(voice)
    total = math.ceil((voice_duration + 1.5) * FPS) / FPS
    cues = word_boundaries(boundaries, 0.45, 0.45 + voice_duration)
    srt = work / "captions.srt"
    ass = work / "overlay.ass"
    write_srt(cues, srt)
    write_ass(title, total, cues, ass)
    order = panel_order(index)
    metadata = {
        "status": "local-review-only", "episode_id": episode_id, "version": "v1", "title": f"{title} | Parenting Rewind",
        "description": f"{hook} A practical pause-and-rewind response for parents.\n\nGeneral parenting education; every child and family is different.",
        "audience_intent": "Adults and parents; not directed to children", "education_scope": "General parenting education only; not personalised therapy, diagnosis, or medical advice.",
        "narration": {"type": "synthetic", "voice": VOICE, "rate": "-5%", "pitch": "-1Hz", "transcript": narration, "new_speech_generation_calls": 1},
        "research": {"reviewed_on": "2026-08-23", "source": SOURCES[source_key], "claim_limits": ["The suggested wording is an example, not a guarantee.", "Families should adapt expectations to age, development, safety and individual needs."]},
        "artwork": {"primary_asset": str(ASSETS[asset_key].relative_to(PROJECT)), "asset_key": asset_key, "panel_order": order, "new_image_generation_calls": 0},
        "music": {"type": "original locally synthesized emotional score", "narration_sidechain_ducking": True, "ambient_background_noise": False, "sound_effects": False},
        "captions": {"burned_in": True, "sidecar": str(srt.relative_to(PROJECT)), "timing_source": "speech-service word boundaries"},
        "published": False, "upload_authorized": False,
    }
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    panels = split_panels(asset_key)
    render_video(panels, order, total, voice, ass, output, work)
    sha = hashlib.sha256(output.read_bytes()).hexdigest().upper()
    metadata["output"] = {"file": str(output.relative_to(PROJECT)), "duration_seconds": total, "sha256": sha}
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = validate(output, total, srt, meta_path, work)
    return {"episode": episode_id, "status": "completed", "output": str(output), "duration_seconds": report["duration_seconds"]}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1, help="1-based batch item")
    parser.add_argument("--count", type=int, default=len(EPISODES))
    args = parser.parse_args()
    if not MUSIC.exists():
        raise FileNotFoundError(MUSIC)
    for key, path in ASSETS.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing {key} asset: {path}")
    start = max(0, args.start - 1)
    end = min(len(EPISODES), start + max(0, args.count))
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    ledger_path = WORK_ROOT / "batch-ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"authorized": True, "upload_authorized": False, "results": []}
    by_id = {item["episode"]: item for item in ledger["results"]}
    for index in range(start, end):
        print(f"Producing batch item {index + 1}/{len(EPISODES)}: {EPISODES[index][0]}", flush=True)
        try:
            result = await produce(index, EPISODES[index])
        except Exception as error:
            result = {"episode": f"batch-item-{index + 1:03d}-{EPISODES[index][0]}", "status": "failed", "error": str(error)}
            print(f"FAILED: {result}", file=sys.stderr, flush=True)
        by_id[result["episode"]] = result
        ledger["results"] = list(by_id.values())
        ledger["updated_on"] = "2026-08-23"
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
