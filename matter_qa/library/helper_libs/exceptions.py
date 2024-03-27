
class ReliabiltyTestError(Exception):
    """A base class for MyProject exceptions."""

class IterationError(ReliabiltyTestError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.iteration_kwarg = kwargs.get('iteration_kwarg', None)
        
#TODO : This error has to used fro partial execution
class TestCaseError(ReliabiltyTestError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.test_case_kwarg = kwargs.get('test_case_kwarg',None)

class TestCaseExit(ReliabiltyTestError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.test_case_kwarg = kwargs.get('test_case_kwarg')
        self.kwargs

    def __str__(self):
        return f"Error: Buildcontroller is failed with {self.kwargs['error']} "