
import random 

class RemarksAnalyzer(object):

    @classmethod
    def get_benchmark_comments(cls):
        return {
        '80': [
            "You're in the champion zone! You are a master at your game!",
            "Keep on crushing it! Your performance is stunning!",
            "You aced it! You  deserve a high-five!",
            "Give yourself a round of applause.Keep shining!",
            "Keep doing what you're doing; it's giving mastery.",
            "Every day you raise the bar.  You're a total rockstar!",
            "Let's count your wins, you're doing amazing",
            "Look who is nailing it! Your practice is making steady progress.",
            "Super proud of you!-Look at you reaching for the stars. "
            ],
        '68': [
            "Good job! Your practice is being perfected.",
            "Keep doing what you're doing; it'll pay off! ",
            "Every day you raise the bar.  You're almost there!",
            "Your practice is making steady  progress. Good job!",
            "Let's count your wins, you're steadily improving."
        ],
        '40': [
            "Winners have two things - definite goals and a burning desire to achieve them. Guess who has both? You do!",
            "Every time you practice, you're adding fuel to your success fire. Let's go again",
            "The goal is to get better, and that happens only with practice.",
            "The more you practice, the better you'll get each time you try.",
            "Every question you get wrong now is one you'll likely get right on exam day. Chin up!",
            "Don't worry if your practice test scores aren't perfect. That's why we practice - to identify what you need to improve."
            "It's just a little bumpy road. Keep practicing and you'd be pushing the stars!",
            "Give it another shot; you're close to excellence."
        ],
        '0': [
            "Take a breath and try again. Practice makes perfect.",
            "When you know better, you do better. You've got this, keep practicing.",
            "We'll take it one practice step at a time. You've got this!",
            "This score is your starting point. With more practice, you can improve.",
            "Everyone starts somewhere. Keep practicing, and you'll get there.",
            "An error on the first try means excellence on the next.",
            "Every question you get wrong now is one you'll likely get right on exam day. Chin up!",
            "Don't worry if your practice test scores aren't perfect. That's why we practice - to identify what you need to improve."
        ]
    }

    @staticmethod
    def determine_remarks(score) -> str:
        for percentile, comments in sorted(RemarksAnalyzer.get_benchmark_comments().items(), reverse=True):
            if score >= int(percentile):
                return random.choice(comments)
        

    @staticmethod
    def determine_percentage_change(new_score, previous_score) -> str:
        
        percentage = int(abs(new_score - previous_score))

        if previous_score == -1 or percentage == 0:
            return ''
        
        change = 'increased by' if new_score > previous_score else 'decreased by'
        good_words = ['Great Job!', 'Awesome!', 'Kudos!', 'Nice!']
        bad_words = ['Aw!', 'Sorry but,', 'Sadly,']

        intro = random.choice(good_words) if new_score > previous_score else random.choice(bad_words)

     
        return f"{intro} Your performance {change} {percentage}%! "
    

    @staticmethod
    def add_remarks_to_test(new_test, old_test):
        #NOTE: Look at the route that saves a test, we need to do things in 
        # in compounding mode or the metadata will be overriden
        new_score = new_test.score_acquired
        old_score = old_test.score_acquired if old_test else -1
        remark = RemarksAnalyzer.determine_percentage_change(new_score, old_score) + RemarksAnalyzer.determine_remarks(new_score)

        meta = {}
        meta['out_time'] = new_test.meta.get('out_time', 0)
        meta['topic_analytics'] = new_test.meta.get('topic_analytics', {})
        meta['remarks'] = remark
        new_test.meta = meta
        new_test.save()


