"""Resumable varied production after the ordinary upload queue was exhausted."""
import asyncio
import json
from produce_redesigned_bundle_02_to_06 import WORK_ROOT, produce

CTA = 'If this helped, like and subscribe for more practical Parenting Rewind ideas.'
EPISODES = [
    dict(number=90, slug='picture-book-conversation-not-test',
         title='Make Picture-Book Time a Conversation, Not a Test',
         asset='evening-reading-father-son-storyboard-01.png', grid=[3,2], order=[5,1,2,4,3,5],
         source=dict(organization='American Academy of Pediatrics / HealthyChildren.org',
                     title='Playful Reading Tips: 4 Ways to Engage Your Child in the Magic of Books',
                     url='https://www.healthychildren.org/English/family-life/power-of-play/Pages/playful-reading-tips-ways-to-engage-your-child-in-the-magic-of-books.aspx'),
         narration=[
             'Your preschooler interrupts a picture book to talk about a tiny animal in the corner. You were hoping to finish the story.',
             'Rushing past every comment or testing every word can turn a shared moment into a performance.',
             'Pause. Their curiosity can become part of the reading, even before they can recognize the words.',
             'Try: You noticed that little animal. What do you think it is doing? Leave space for their answer instead of supplying it immediately.',
             'Look at the pictures together, follow an interesting detail, and wonder what could happen next. The conversation belongs in book time too.', CTA]),
    dict(number=91, slug='describe-chore-without-sibling-comparison',
         title='Correct the Chore Without Comparing Siblings',
         asset='laundry-father-two-children-storyboard-01.png', grid=[3,2], order=[1,0,2,4,3,5],
         source=dict(organization='Iowa State University Extension, hosted by Kansas State University Extension',
                     title='Understanding Children: Sibling Rivalry',
                     url='https://www.harvey.k-state.edu/family_and_child_development/documents/SiblingRivalry.pdf'),
         narration=[
             'One child is folding towels, while the other has left a pile of socks. Why cannot you be more like your sister is ready to slip out.',
             'That comparison can turn a household job into a contest between the children.',
             'Pause and take the sibling out of the correction. Name the unfinished task without ranking either child.',
             'Try: These socks still need matching. Please start with this pair. Give help if the task is beyond their current skills.',
             'You can notice each child\'s contribution without praising one at the other\'s expense. Keep the direction about the job, not who is the better child.', CTA]),
    dict(number=92, slug='teen-argument-break-with-return-time',
         title='Pause the Teen Argument and Agree When to Return',
         asset='teen-curfew-father-daughter-storyboard-01.png', grid=[3,2], order=[1,2,0,3,4,5],
         source=dict(organization="The Royal Children's Hospital Melbourne",
                     title='Understanding behaviour: teens and young people',
                     url='https://www.rch.org.au/kidsinfo/fact_sheets/Challenging_behaviour_teenagers/'),
         narration=[
             'A disagreement with your teenager keeps circling. Both voices are getting louder, but neither person feels understood.',
             'Trying to win the argument right now can leave less room to solve the actual problem.',
             'Pause the discussion when emotions are high. A break should lead back to a conversation, not become days of silence.',
             'Try: I want to hear you, and I need to calm down. Can we come back to this after dinner? Choose a time you can keep.',
             'When you return, listen to their point of view and discuss one concern at a time. Keep necessary safety limits clear while working on the relationship.', CTA]),
]

for spec in EPISODES:
    spec.update(reviewed_on='2026-09-13', upload_authorized=True, mirror_to_onedrive=True,
                recycled_visuals_approved=True, new_image_generation_calls=0,
                generation_prompt_record='production-assets/reuse-audit-90-to-92.md')


async def main():
    results=[]
    for spec in EPISODES:
        result=await produce(spec)
        results.append(result)
        (WORK_ROOT/'bundle-90-to-92-ledger.json').write_text(json.dumps({'results':results},indent=2))
        print(json.dumps(result),flush=True)


if __name__=='__main__':
    asyncio.run(main())
