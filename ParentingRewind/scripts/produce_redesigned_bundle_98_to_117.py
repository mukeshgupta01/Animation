"""Finite user-authorized 20-episode batch; review before any verified mirror."""
import argparse
import asyncio
import json
from produce_redesigned_bundle_02_to_06 import PROJECT, WORK_ROOT, produce
from produce_redesigned_bundle_96_to_97 import prepare_portrait_panels as base_prepare, CTA
from PIL import Image

def prepare_portrait_panels(spec):
    # Measured boundaries: these generated sheets have a slightly taller lower row.
    if spec['number'] in (103,110):
        work=WORK_ROOT/f"parenting-rewind-redesign-{spec['number']:02d}-{spec['slug']}"/'source-panels'
        work.mkdir(parents=True,exist_ok=True)
        with Image.open(PROJECT/'production-assets'/spec['asset']) as im:
            xs=[(7,500),(521,1013),(1035,1529)]
            ys=[(7,486),(507,1017)]
            for i in range(6):
                row,col=divmod(i,3);x1,x2=xs[col];y1,y2=ys[row]
                im.crop((x1,y1,x2,y2)).convert('RGB').save(work/f'panel-{i}.jpg',quality=95)
    base_prepare(spec)

def source(title, url):
    organization = ('American Academy of Pediatrics / HealthyChildren.org' if 'healthychildren' in url
                    else 'Australian eSafety Commissioner' if 'esafety' in url
                    else 'StopBullying.gov / US Department of Health and Human Services' if 'stopbullying' in url
                    else 'Raising Children Network')
    return dict(organization=organization, title=title, url=url)

def episode(number, slug, title, age, asset, order, research, labels, narration, description):
    return dict(number=number, slug=slug, title=title, age_group=age, asset=asset+'.png',
                grid=[3,2], order=order, source=research, beat_labels=labels.split('|'),
                narration=narration+[CTA], description=description, reviewed_on='2026-09-25',
                upload_authorized=True, mirror_to_onedrive=False, title_duration=5.0,
                recycled_visuals_approved=number not in (100,103,104,110,115),
                new_image_generation_calls=int(number in (100,103,104,110,115)),
                generation_prompt_record='production-assets/asset-audit-98-to-117.md')

EPISODES = [
episode(98,'give-time-to-warm-up','Give Them Time to Warm Up','preschool',
 'preschool-body-autonomy-greeting-father-daughter-grandmother-storyboard-01',[0,1,2,3,5,4],
 source('Shyness in children: how to help a shy child','https://raisingchildren.net.au/preschoolers/behaviour/common-concerns/shyness'),
 'A QUIET ARRIVAL|DROP THE LABEL|ALLOW SOME TIME|STAY NEARBY|SMALL STEPS|KEEP ENCOURAGING',[
 "A visitor arrives, and your preschooler stays close to you. You explain, She is always so shy, while she listens.",
 "Pause before turning one quiet moment into a label. Some children need more time to feel comfortable around people.",
 "Try: She is getting used to things. We can stay together for a little while. Let her watch first.",
 "Offer a small way to join, like showing a book, without demanding a performance or comparing her with another child.",
 "Notice a step she chooses. If social situations regularly cause distress or stop everyday activities, ask a qualified professional for guidance."],
 'A quiet greeting does not need a permanent label. Offer time, nearby support and a small invitation to join.'),
episode(99,'repair-after-spilled-plant','After the Mistake, Make Repair Possible','school-age',
 'honesty-father-son-storyboard-01',[0,2,3,4,5,3],
 source('Consequences and positive child behaviour','https://raisingchildren.net.au/school-age/behaviour/rules-consequences/consequences'),
 'THE SPILLED SOIL|STEADY YOUR RESPONSE|NAME THE REPAIR|CHOOSE A SAFE JOB|WORK TOGETHER|RESPONSIBILITY CAN GROW',[
 "Your child knocks over a plant, and soil covers the floor. You are tempted to take away something completely unrelated.",
 "Pause. Once everyone is safe, connect the response to what actually happened. The plant needs care and the floor needs cleaning.",
 "Try: The soil spilled. Let us work out how to put this right. Keep the focus on repair, not character.",
 "Give your child a safe, manageable part, such as fetching a brush. Handle sharp pieces or other hazards yourself.",
 "Help where needed, then notice their contribution. A related response gives them a way to practise responsibility instead of only feeling bad."],
 'Use an everyday spill to practise safe, proportionate repair. This lesson focuses on responsibility after a mistake, rather than interrogating a child about honesty.'),
episode(100,'knock-before-entering-teen-room','Knock Before Entering Your Teen\'s Room','teen',
 'teen-privacy-father-son-storyboard-01',[0,1,2,3,4,5],
 source('Privacy, trust and monitoring: 9-18 years','https://raisingchildren.net.au/teens/communicating-relationships/family-relationships/privacy-trust-teen-years'),
 'THE CLOSED DOOR|NOTICE THEIR SPACE|PAUSE AT THE DOOR|KNOCK AND WAIT|RESPECT GOES BOTH WAYS|AGREE ON BOUNDARIES',[
 "Your teenager closes the bedroom door, and you walk straight in. Their frustration does not automatically mean they are hiding something.",
 "Growing up includes wanting personal space. You can respect that while still staying involved in your teenager's life.",
 "Rewind the moment. For an ordinary visit, knock and wait for an answer before entering. Ask whether now is a good time.",
 "Try: I want to respect your space. Can we agree how we will check in and when I need to know more?",
 "Discuss safety exceptions calmly in advance. Privacy is not the same as leaving a teenager without support or ignoring a serious concern."],
 'A closed door can be an ordinary request for space. Practise knocking, waiting and discussing privacy alongside reasonable safety responsibilities.'),
episode(101,'name-storybook-feelings','Find Feeling Words in a Story','preschool',
 'evening-reading-father-son-storyboard-01',[5,0,2,4,3,5],
 source('Preschoolers and emotions: play ideas','https://raisingchildren.net.au/preschoolers/play-learning/play-preschooler-development/emotions-play-preschoolers'),
 'A QUIET STORY|MORE THAN HAPPY OR SAD|NOTICE THE CHARACTER|OFFER A WORD|LET THEM WONDER|KEEP IT PLAYFUL',[
 "A story character loses something precious. Your preschooler watches the picture, and you have a chance to explore a feeling together.",
 "You do not need a quiz or a correct answer. Start with what the character's face or actions make you wonder.",
 "Try: I wonder if she feels disappointed. She wanted that to happen. What do you notice about this picture?",
 "Let your child offer a different idea, or simply listen. Use everyday words they can hear again during real experiences.",
 "Books and pretend play make room to explore feelings when nobody is in trouble. Keep the conversation brief, warm and playful."],
 'Use a story to introduce feeling words without testing your preschooler. The aim is emotional vocabulary, not reading performance.'),
episode(102,'notice-everyday-gratitude','Make Gratitude an Everyday Conversation','school-age',
 'kitchen-siblings-storyboard-01',[5,0,2,4,3,5],
 source('Beyond Thanks: 5 Ways to Nurture Gratitude in Children','https://www.healthychildren.org/English/healthy-living/emotional-wellness/Building-Resilience/Pages/how-to-practice-gratitude.aspx'),
 'AROUND THE TABLE|MORE THAN MANNERS|START WITH YOURSELF|NOTICE SOMEONE\'S CARE|INVITE A REAL ANSWER|SMALL THINGS COUNT',[
 "Dinner is ready, and you remind your child to say thank you. Gratitude can go beyond getting the polite words right.",
 "Instead of demanding a grateful attitude, describe something you appreciated today. Make it ordinary, specific and honest.",
 "Try: I appreciated you bringing the napkins while I finished cooking. That made our busy evening a little easier.",
 "Invite your child to name a person or moment they valued. Listen without correcting their answer or comparing it with yours.",
 "A difficult day can still have one good moment. Appreciation does not mean pretending disappointment, anger or sadness never happened."],
 'Try a small family conversation about what or whom you appreciated. Gratitude is an invitation to notice care, not a demand to deny difficult feelings.'),
episode(103,'pause-before-teen-purchase','Help Your Teen Pause Before Buying','teen',
 'teen-money-mother-daughter-storyboard-01',[0,1,2,3,4,5],
 source('Kids and Money: Help Your Child Learn Good Financial Habits','https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline/Pages/money-matters-helping-your-kids-create-good-habits.aspx'),
 'THE MUST-HAVE ITEM|SKIP THE LECTURE|LOOK AT THE CHOICE|CHECK THE WHOLE COST|MAKE ROOM TO WAIT|PRACTISE DECIDING',[
 "Your teenager wants new headphones right now. Calling the purchase ridiculous can end the conversation before any money skills get practised.",
 "Pause and ask what matters about the item. Then look together at the price and the money actually available.",
 "Try: If you choose this, what will you have left for the other things you planned? Let them do the thinking.",
 "Compare options and consider waiting before deciding. You can set your own spending boundary without mocking what your teenager likes.",
 "The aim is supported practice with choices, saving and trade-offs. Adapt the conversation to your family's resources, without promising extra money."],
 'Turn an impulse purchase into a conversation about available money and competing goals. A parenting example, not personalised financial advice.'),
episode(104,'join-childs-screen-viewing','Join the Screen-Time Conversation','preschool',
 'preschool-coview-father-son-storyboard-01',[0,1,2,3,5,4],
 source('Watch Together: Co-Viewing Media With Your Child','https://www.healthychildren.org/English/family-life/Media/Pages/watch-together.aspx'),
 'WHAT ARE THEY WATCHING?|JOIN WITH CURIOSITY|TALK ABOUT THE STORY|CONNECT IT TO LIFE|TAKE PLAY OFFSCREEN|KEEP YOUR LIMITS',[
 "Your young child is watching a programme, and you only notice the screen when it is time to switch it off.",
 "When your family chooses media time, try sharing some of it. Find out what has captured your child's attention.",
 "Ask a simple question about the story, or explain something confusing. Leave room for their thoughts instead of talking over everything.",
 "Connect the idea to everyday life. If characters build something, perhaps you can explore building with blocks after the programme.",
 "Watching together does not make every programme suitable or remove the need for limits. Choose appropriate content and protect time for other activities."],
 'Co-viewing means engaging with the content together. This episode focuses on conversation and offscreen connections, rather than negotiating the ending.'),
episode(105,'keep-child-out-of-adult-messages','Your Child Is Not the Messenger','school-age',
 'separation-reassurance-family-storyboard-01',[1,0,2,3,5,4],
 source('Divorce and Separation: How to Help Your Child Adjust','https://www.healthychildren.org/English/family-life/family-dynamics/types-of-families/Pages/adjusting-to-divorce.aspx'),
 'AN ADULT MESSAGE|NOTICE THE BURDEN|TAKE IT BACK|USE AN ADULT CHANNEL|KEEP THE CHILD INFORMED|LET THEM BE THE CHILD',[
 "You hand your child a message for their other parent about a changed arrangement. They look worried about the answer.",
 "Pause before putting them between adults. Practical disagreements and difficult messages belong with the grown-ups responsible for sorting them out.",
 "Try: You do not need to carry that message. I will handle it through the appropriate adult communication channel.",
 "Tell your child the part they need to know, such as the next pickup plan, without blame or private adult details.",
 "Use arrangements that fit your family's safety needs. Your child can have feelings and questions without becoming the messenger or peacekeeper."],
 'Keep children out of adult messaging after separation. Share clear child-relevant plans and use safe, appropriate adult communication arrangements.'),
episode(106,'support-teen-after-hurtful-message','When Your Teen Shows You a Hurtful Message','teen',
 'teen-phone-boundary-mother-son-storyboard-01',[0,1,2,3,4,5],
 source('Bullying online','https://www.esafety.gov.au/young-people/cyberbullying'),
 'THE HURTFUL MESSAGE|DO NOT BLAME DISCLOSURE|STAY WITH THEM|PLAN THE NEXT STEP|REPORT AND GET SUPPORT|KEEP CHECKING IN',[
 "Your teenager shows you a cruel message. Reaching straight for their phone can make asking for help feel like a punishment.",
 "Start with support: I am glad you showed me. Let us work out what will help you feel safer now.",
 "Avoid sending an angry reply. For ordinary abusive messages, help keep the details needed to report what happened before blocking accounts.",
 "Report through the service and seek trusted support. Do not copy or share sexual images of anyone under eighteen; get specialist guidance.",
 "Check in again after the first conversation. Serious threats need urgent help. In Australia, eSafety provides guidance for reporting serious online bullying."],
 'Support disclosure, avoid retaliation and plan reporting together. Evidence handling depends on the content: never copy or redistribute sexual images of minors. Australian reporting guidance is linked below.'),
episode(107,'welcome-imaginary-friend','An Imaginary Friend Can Be Part of Play','preschool',
 'child-led-play-father-daughter-storyboard-01',[3,0,2,4,5,3],
 source('Imaginary friends and children','https://raisingchildren.net.au/preschoolers/behaviour/friends-siblings/imaginary-friends'),
 'A PRETEND COMPANION|GET CURIOUS|JOIN THE STORY|KEEP REAL LIMITS|MAKE ROOM FOR PLAY|FOLLOW THEIR INTEREST',[
 "Your preschooler says an invisible friend is coming along for the game. You wonder whether you should correct the whole story.",
 "An imaginary companion can be part of childhood play. You can be curious without insisting the character is real.",
 "Try: Tell me about your friend's adventure. Let your child explain as much or as little as they want.",
 "Keep ordinary limits. If the imaginary friend is blamed for a mess, you can still invite your child to help tidy.",
 "Enjoy the imagination while making room for real relationships and activities. If you are concerned about distress or daily functioning, seek professional advice."],
 'Respond with curiosity to a preschooler\'s imaginary companion while keeping ordinary household limits. This is about pretend play, not diagnosing unusual experiences.'),
episode(108,'ask-about-art-not-perfection','Ask About the Making, Not the Perfect Picture','school-age',
 'art-studio-father-daughter-storyboard-01',[4,0,2,3,5,4],
 source('Creative play and activities for school-age children','https://raisingchildren.net.au/school-age/development/creative-development/school-age-creative-activities'),
 'THE PICTURE COMES HOME|SKIP THE SCORE|ASK ABOUT THE PROCESS|LISTEN TO THEIR IDEA|LEAVE ROOM TO EXPERIMENT|CREATIVITY IS EXPLORATION',[
 "Your child brings home artwork, and your first instinct is to rate it or point out what would make it neater.",
 "Pause. Creative work can be about trying an idea, exploring materials and enjoying the making, not producing an adult-looking result.",
 "Try: Tell me about this part. How did you choose those colours? Follow what your child wants to share.",
 "If they want to change something, offer materials and time rather than taking over. Their picture does not need your finishing touches.",
 "You can value their curiosity without calling every result perfect. Make room for experimenting, starting again and deciding what the work means to them."],
 'Talk about creative choices and the experience of making art. Keep ownership with your child instead of turning every picture into an assessment.'),
episode(109,'grow-teen-independence-in-steps','Grow Independence One Step at a Time','teen',
 'teen-curfew-father-daughter-storyboard-01',[0,2,3,4,5,3],
 source('Responsibility: pre-teens and teenagers','https://raisingchildren.net.au/teens/communicating-relationships/family-relationships/shifting-responsibility-teen-years'),
 'A NEW REQUEST|AVOID ALL OR NOTHING|HEAR THE PLAN|AGREE ON SUPPORT|REVIEW THE EXPERIENCE|BUILD GRADUALLY',[
 "Your teenager asks to go somewhere more independently. You feel caught between saying no to everything and agreeing without a plan.",
 "Pause and consider a manageable next step, based on their readiness and the situation, rather than their friends' permissions.",
 "Ask them to explain where they will be, who they will be with and how they will get home safely.",
 "Agree on a check-in and a way to ask for help. Keep expectations clear, realistic and suited to your family.",
 "Afterwards, talk about what worked and what needs adjusting. Responsibility can grow through supported experience; one agreement does not decide every future outing."],
 'Consider a manageable independence step with a clear plan and later review. This is distinct from responding to an already missed curfew.'),
episode(110,'prepare-special-toys-before-playdate','Put Precious Toys Away Before a Playdate','preschool',
 'preschool-playdate-mother-son-storyboard-01',[0,1,2,3,4,5],
 source('Teaching children to share: an age-by-age guide','https://raisingchildren.net.au/toddlers/behaviour/friends-siblings/sharing'),
 'EVERYONE WANTS IT|PLAN BEFORE PLAY|PROTECT A SPECIAL ITEM|CHOOSE SHARED MATERIALS|STAY AVAILABLE|SHARING TAKES PRACTICE',[
 "Two preschoolers reach for the same favourite thing, and sharing suddenly becomes the whole playdate. Preparation can help before friends arrive.",
 "Let your child choose a few precious items to put away. Having something private does not make a child selfish.",
 "Then choose toys or materials they are happy to use together. Explain that these are the things available for shared play.",
 "Stay close enough to help with turns and disagreements. Offer another activity when waiting becomes too difficult for either child.",
 "Keep expectations appropriate to their age and abilities. Sharing grows with supported practice, and a little planning can reduce avoidable conflicts."],
 'Prepare shared play materials while allowing a few personal favourites to stay private. This lesson is about prevention before a playdate, not forcing an immediate handover.'),
episode(111,'talk-needs-and-wants-shopping','Talk About Needs and Wants While Shopping','school-age',
 'supermarket-storyboard-01',[0,2,3,4,5,3],
 source('Money management for children','https://raisingchildren.net.au/school-age/family-life/pocket-money/money-management-for-children'),
 'THE SHOPPING LIST|MAKE THINKING VISIBLE|NEEDS AND WANTS|EXPLAIN YOUR CHOICE|PRACTISE WITH SMALL DECISIONS|NO SHAME NEEDED',[
 "Your child asks why you buy one thing and leave another behind. A shopping trip can introduce choices without a money lecture.",
 "Explain the difference between what your family needs and an extra you would enjoy. Use a simple example from today's list.",
 "Try: We planned money for these groceries. That extra is something we want, so we need to decide whether it fits.",
 "Let your child help compare a small choice. Keep adult financial worries with adults; they do not need to solve your budget.",
 "Wanting something is not shameful, and different families have different resources. You are showing how to think about priorities one ordinary decision at a time."],
 'Introduce needs, wants and priorities using an ordinary shopping choice. Keep the example age-appropriate and avoid placing adult financial anxiety on children.'),
episode(112,'be-curious-about-teen-interests','Be Curious About What Your Teen Enjoys','teen',
 'teen-parent-alarm-father-daughter-storyboard-01',[0,2,4,3,5,4],
 source('Staying connected with pre-teens and teenagers','https://raisingchildren.net.au/teens/communicating-relationships/family-relationships/staying-connected-you-your-teen'),
 'AN EVERYDAY OPENING|SET JUDGMENT ASIDE|ASK ONE REAL QUESTION|LET THEM EXPLAIN|ENJOY A SMALL MOMENT|CONNECTION CAN BE ORDINARY',[
 "Your teenager mentions a favourite song, game or hobby, and you immediately explain why you preferred things when you were young.",
 "Pause. You do not have to share every interest to show that their enjoyment matters to you.",
 "Try: What do you like about it? Or, show me the part you enjoy most. Ask because you want to understand.",
 "Let them explain without turning the moment into a test, a lecture or a request for information about everything else.",
 "A short shared moment can be enough. Keep appropriate limits, but leave space for ordinary enjoyment together, not only serious talks when something goes wrong."],
 'Use an everyday interest as a small opportunity to connect. Curiosity does not require liking the same things or abandoning family limits.'),
episode(113,'respond-calmly-to-preschool-swearing','When Your Preschooler Tries a Swear Word','preschool',
 'evening-reading-father-son-storyboard-01',[0,1,2,3,4,5],
 source('Swearing: preschoolers','https://raisingchildren.net.au/preschoolers/behaviour/common-concerns/swearing-preschoolers'),
 'A SURPRISING WORD|KEEP YOUR REACTION SMALL|NOTICE THE REASON|OFFER ANOTHER WAY|MODEL YOUR OWN WORDS|PRACTISE RESPECT',[
 "Your preschooler repeats a swear word, and everyone reacts. A big laugh or shocked lecture can make that word more interesting.",
 "Keep your response calm and consider what is happening. They might be copying, seeking a reaction or trying to express frustration.",
 "If they are upset, help name the feeling and offer another phrase, such as, I am really annoyed about that.",
 "If it is mainly for attention, avoid making a spectacle. Give warm attention to respectful communication at other moments instead.",
 "Keep your family's language expectations simple and model them yourself. Young children need practice; one surprising word is not a verdict on their character."],
 'Keep the reaction proportionate, consider why the word appeared and teach a useful alternative. No swear words are spoken in this episode.'),
episode(114,'keep-body-comments-off-menu','Keep Body Comments Off the Menu','school-age',
 'kitchen-siblings-storyboard-01',[5,1,2,3,4,5],
 source('Helping Kids Cope With Eating Disorders and Body Concerns During the Holidays','https://www.healthychildren.org/English/health-issues/conditions/emotional-problems/Pages/helping-kids-with-eating-disorders-and-other-food-concerns-navigate-holiday-gatherings.aspx'),
 'A FAMILY MEAL|NOTICE THE BODY TALK|CHANGE THE SUBJECT|SET A RESPECTFUL LIMIT|MODEL A DIFFERENT CONVERSATION|MAKE ROOM FOR CONNECTION',[
 "At a family meal, someone comments on a child's body or on how much is on their plate. You can redirect the conversation.",
 "Pause before laughing along. Even casual remarks can make bodies and eating feel like something everyone is entitled to judge.",
 "Try: Let us leave body comments out of dinner. I would love to hear about what you have been enjoying lately.",
 "Notice your own talk too. You can discuss people, interests and everyday experiences without rating your body or somebody else's food.",
 "This is a communication boundary, not a nutrition treatment. If you are worried about your child's eating or health, speak privately with a qualified professional."],
 'Set a simple boundary around body and food commentary at family meals. This general communication example does not replace individual eating-disorder or medical care.'),
episode(115,'agree-teen-chore-ownership','Give Your Teen Ownership of a Household Task','teen',
 'teen-chores-father-daughter-storyboard-01',[0,1,2,3,4,5],
 source('Household chores for kids and teenagers','https://raisingchildren.net.au/toddlers/family-life/routines-rituals/chores-for-children'),
 'THE REMINDER LOOP|MAKE THE TASK CLEAR|PLAN TOGETHER|AGREE WHAT DONE MEANS|GIVE THEM ROOM|NOTICE THE CONTRIBUTION',[
 "You keep reminding your teenager about the laundry, but neither of you has agreed what the job includes or when it needs doing.",
 "Pause the running commentary. Choose a suitable responsibility together and explain how it contributes to the household.",
 "Try: Could you own the clean towels this week? Let us agree where they go and a time that works.",
 "Check they know the steps, then give them space to practise. Agree on a reminder system instead of hovering over every move.",
 "Thank them for the contribution and review the plan if it is not working. The aim is a useful life skill, with expectations matched to ability."],
 'Move from repeated reminders to a clearly agreed household responsibility. Teach any missing steps and give your teenager room to practise.'),
episode(116,'keep-home-language-in-stories','Keep Your Home Language in Story Time','preschool',
 'library-grandmother-granddaughter-storyboard-01',[0,2,3,0,5,4],
 source('Benefits of bilingualism and multilingualism','https://raisingchildren.net.au/babies/connecting-communicating/bilingualism-multilingualism/bilingualism'),
 'A FAMILIAR STORY|YOUR LANGUAGE BELONGS|SHARE WORDS NATURALLY|ENJOY THE CONVERSATION|KEEP FAMILY CONNECTION|MAKE IT PART OF LIFE',[
 "Your preschooler enjoys a story with a grandparent, and you wonder whether using your home language might get in the way of English.",
 "Using a heritage language at home does not prevent children from learning English. It can also support connection with family and culture.",
 "Share stories, songs and everyday conversation in a language you feel comfortable using. You do not need to turn it into lessons.",
 "Let your child respond and enjoy the exchange. Hearing more than one language is part of daily life for many families.",
 "Keep opportunities warm and regular, without testing every word. If you have concerns about communication development, ask a qualified professional familiar with multilingual children."],
 'Make space for a home or heritage language in family stories and everyday conversation. This is general encouragement, not an assessment of a child\'s language development.'),
episode(117,'help-child-be-safe-bystander','When Your Child Sees Someone Being Bullied','school-age',
 'school-peer-exclusion-father-daughter-storyboard-01',[0,2,3,4,5,3],
 source('Bystanders to Bullying','https://www.stopbullying.gov/prevention/bystanders-to-bullying'),
 'THEY SAW IT HAPPEN|HEAR THEIR WORRY|SAFETY COMES FIRST|CHOOSE A HELPFUL ACTION|INVOLVE A TRUSTED ADULT|CHECK IN AGAIN',[
 "Your child says someone at school was being bullied, but they did not know what to do. Start by hearing their worry.",
 "Do not demand a dramatic confrontation. They can help without putting themselves in danger or trying to handle the whole situation alone.",
 "Discuss a safe next step: get a trusted adult, stay near the child being targeted, or check on them afterwards.",
 "They can avoid joining the laughter or sharing hurtful material. Practise how to tell a teacher clearly what they saw.",
 "Adults remain responsible for responding to bullying. Thank your child for speaking up, follow through with support and ask how things are going later."],
 'Plan safe ways to support a peer and involve a trusted adult. Children should not be expected to confront danger or solve bullying on their own.'),
]

async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--start',type=int,default=98)
    parser.add_argument('--count',type=int,default=20)
    parser.add_argument('--rebuild',action='store_true')
    args=parser.parse_args()
    selected=[s for s in EPISODES if args.start<=s['number']<args.start+args.count]
    for spec in selected:
        if args.rebuild:spec=dict(spec,force_rebuild=True)
        prepare_portrait_panels(spec)
        result=await produce(spec)
        path=PROJECT/'metadata'/f"parenting-rewind-redesign-{spec['number']:02d}-{spec['slug']}-v1.json"
        data=json.loads(path.read_text(encoding='utf-8'))
        data['description']=(spec['description']+'\n\nGeneral parenting education for adults; adapt to your child and circumstances.'
            +'\n\nSource: '+spec['source']['title']+'\n'+spec['source']['url']
            +'\n\nOriginal illustrative visuals, synthetic narration and original music.\n'+CTA+'\n\n#ParentingRewind #ParentingTips')
        data['age_group']=spec['age_group']
        data['tags']=['Parenting Rewind','parenting tips',spec['age_group']+' parenting']
        data['artwork']['framing']='Full panel on soft portrait background; faces and hands preserved.'
        path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(json.dumps(result),flush=True)

if __name__=='__main__':asyncio.run(main())
