
class ReliabiltyTestError(Exception):
    """A base class for MyProject exceptions."""

class IterationError(ReliabiltyTestError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.args = args
        self.iteration_kwarg = kwargs.get('iteration_kwarg', None)
    
    def __str__(self):
        return f"Error: Iteration is failed {self.args[0]} "
        
#TODO : This error has to used fro partial execution
class TestCaseError(ReliabiltyTestError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.args = args
        self.iteration_kwarg = kwargs.get('iteration_kwarg', None)
    
    def __str__(self):
        return f"Error: testcase is failed {self.args[0]} "

class TestExitError(ReliabiltyTestError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.test_case_kwarg = kwargs.get('test_case_kwarg')
        self.kwargs

    def __str__(self):
        return f"Error: Buildcontroller is failed with {self.kwargs['error']} "