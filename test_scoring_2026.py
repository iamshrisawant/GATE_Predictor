import sys
import os

sys.path.append(os.getcwd())
import app.services.extraction as extraction
import app.services.scoring as scoring

tests = [
    {
        "code": "EC",
        "key": "test/G412P96-EC26S72105100-answerKey.pdf",
        "paper": "test/G412P96-EC26S72105100-questionPaper.pdf",
        "url": "https://cdn.digialm.com//per/g01/pub/585/touchstone/AssessmentQPHTMLMode1//GATE2568/GATE2568S7D7966/17712265346221341/EC26S72105100_GATE2568S7D7966E2.html"
    },
    {
        "code": "CS",
        "key": "test/G368E21-CS26S42101001-answerKey.pdf",
        "paper": "test/G412P96-EC26S72105100-questionPaper.pdf", # Might fail since wrong paper but we can check if it tries scoring
        "url": "https://cdn.digialm.com//per/g01/pub/585/touchstone/AssessmentQPHTMLMode1//GATE2565/GATE2565S4D9886/17706396805423777/CS26S42101001_GATE2565S4D9886E1.html"
    },
    {
        "code": "DA",
        "key": "test/G368E21-DA26S82101040-answerKey.pdf",
        "paper": "test/G368E21-DA26S82101040-questionPaper.pdf",
        "url": "https://cdn.digialm.com//per/g01/pub/585/touchstone/AssessmentQPHTMLMode1//GATE2569/GATE2569S8D7711/17712323440501573/DA26S82101040_GATE2569S8D7711E1.html"
    }
]

def run():
    for t in tests:
        print(f"\n--- SCORE TEST: {t['code']} ---")
        try:
            with open(t['key'], 'rb') as kf, open(t['paper'], 'rb') as pf:
                schema = extraction.extract_answer_key(kf, paper_code=t['code'], paper_source=pf)
            score_data = scoring.calculate_score(t['url'], schema)
            
            if 'error' in score_data:
                print(f"Error scoring {t['code']}: {score_data['error']}")
            else:
                summary = score_data['summary']
                print(f"Score for {t['code']}: {summary.get('total_score')} (Attempted: {summary.get('attempted')})")
        except Exception as e:
            print(f"Failed {t['code']}: {e}")

if __name__ == '__main__':
    run()
