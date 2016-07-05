import subprocess32

class UnifiableProlog:
    prolog_file = ""#./unify.pl

    def __init__(self, p_fl):
        self.prolog_file = p_fl

    def __generate_prolog_unification_symbols(self, math_query, math_data):
        return "%s = %s" % (math_query, math_data)

    def is_unified(self, math_query, math_data):
        '''
            Example of math_query or math_data: aX+b
        '''
        math_prolog_unif = self.__generate_prolog_unification_symbols(math_query, math_data)

        #Open subprocess
        p = subprocess32.Popen([self.prolog_file, math_prolog_unif], 
        stdout=subprocess32.PIPE,
        stderr=subprocess32.PIPE)

        output, err = p.communicate()
        isUnifiable = any(output.startswith(flag) for flag in ["0", "1"]) and \
                         bool(int(output[0]))

        return isUnifiable

