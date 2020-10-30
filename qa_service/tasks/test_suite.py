import time
from celery import shared_task
from celery.execute import send_task


## Dispatch functie
@shared_task
def run_testsuite():
    tests = []

    ### Test celery taken toevoegen aan list 'tests' ###
    # [TEST] Getoonde FSN controleren in snomedbrowser.nl
    tests.append(send_task('qa_service.tasks.snomedbrowser.checkFSN', kwargs = {
            'concept_list': [
                        {'id':'18213006', 'fsn': 'elektriciteit (fysische kracht)'},
                        {'id':'18213006', 'fsn': 'elektricity (fout)'},
                        {'id':'74400008', 'fsn': 'appendicitis (aandoening)'},
                    ]
        }))
    # [TEST] Getoonde Patientvriendelijke term controleren in snomedbrowser.nl
    tests.append(send_task('qa_service.tasks.snomedbrowser.checkPTFriendly', kwargs = {
            'concept_list': [
                        {'id':'74400008', 'pt': 'blindedarmontsteking'},
                    ]
        }))




    ### Taken uitvoeren ###
    go_wait = False
    while True:
        # Initieel 2 seconden de tijd geven om taken uit te voeren
        time.sleep(2)
        # Voor elke tast:
        for test in tests:
            # Zodra er 1 test niet klaar is: wachten.
            if test.status != 'SUCCESS': go_wait = True

        # Als ALLE testen klaar zijn: breek de loop
        if go_wait == False: break

    # Print het resultaat van iedere test - TODO moet een webhook worden.
    # Elke test moet een resultaat opleveren in het formaat:
    # {
    #       'Percentage geslaagd'   : int,
    #       'Foutmeldingen'         : [{
    #           }]
    # }
    #
    print("RESULT [run_testsuite]:")
    output = []
    for test in tests:
        print(test.result)
        output.append(test.result)
    
    return output