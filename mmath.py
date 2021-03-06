import math
import llvm.core
import compiler 
from PyllvmError import *
llTruthType    = llvm.core.Type.int(1)
llVoidType     = llvm.core.Type.void()
llIntType      = llvm.core.Type.int()
llFloatType    = llvm.core.Type.float()
llFVec4Type    = llvm.core.Type.vector(llFloatType, 4)
llFVec4PtrType = llvm.core.Type.pointer(llFVec4Type)
llIVec4Type    = llvm.core.Type.vector(llIntType, 4)
#
# Intrinsic math functions
#
intrinsics = {
    # Name    : ( ret type , arg types
      'abs'   : ( int    , [ int        ] )
    , 'pow'   : ( int    , [ int        ] )
    , 'exp'   : ( int    , [ int        ] )
    , 'log'   : ( int    , [ int, int   ] )
    , 'sqrt'  : ( int    , [ int        ] )
    , 'mod'   : ( int    , [ int, int   ] )
    , 'int'   : ( float  , [ int        ] )
    , 'float' : ( int    , [ float      ] )
    , 'range' : ( list   , [ int        ] )
    , 'zeros' : ( list   , [ int        ] )
}

class mMathFuncs(object):
    def __init__(self, codegen):
        self.codeGen = codegen
    def emitabs(self, node):
        if(len(node.args)!=1):
            raise PyllvmError("mmath: one argument to abs")
        ty = self.codeGen.typer.inferType(node.args[0])
        v = self.codeGen.visit(node.args[0])
        if(ty==int):
            return self.codeGen.builder.call(self.codeGen._mabs, [v])
        elif(ty==float):
            return self.codeGen.builder.call(self.codeGen._fmabs, [v])
        raise PyllvmError("mmath: unhandled type for abs") 
    def emitmod(self, node):
        if(len(node.args)!=2):
            raise PyllvmError("mmath: 2 arguments needed for mod")
        lty = self.codeGen.typer.inferType(node.args[0])
        rty = self.codeGen.typer.inferType(node.args[1])
        if lty!=rty:
            raise PyllvmError("mmath: both arguments must match type for mod")
        l = self.codeGen.visit(node.args[0])
        r = self.codeGen.visit(node.args[1])
        if(rty==int):
            return self.codeGen.builder.srem(l, r)
        elif(rty==float):
            return self.codeGen.builder.frem(l,r)
        raise PyllvmError("mmath: unhandled type for mod") 
   

    def emitpow(self, node):
        if(len(node.args)!=2):
            raise PyllvmError("mmath: 2 arguments needed for pow")
        lty = self.codeGen.typer.inferType(node.args[0])
        rty = self.codeGen.typer.inferType(node.args[1])
        
        l = self.codeGen.visit(node.args[0])
        r = self.codeGen.visit(node.args[1])
        if rty == int:
            r = self.codeGen.builder.sitofp(r, llFloatType)
        elif rty != float:
            raise PyllvmError("mmath: exponent must be numerical")
        if(lty==int):
            l = self.codeGen.builder.sitofp(l, llFloatType)
            return self.codeGen.builder.fptosi(self.codeGen.builder.call(self.codeGen._fpow, [l,r]),  llIntType)
        elif(lty==float):
            return self.codeGen.builder.call(self.codeGen._fpow, [l,r])
        raise PyllvmError("mmath: base for exponent must be numerical") 
    
    def emitlog(self, node):
        if(len(node.args)!=1):
            raise PyllvmError("mmath: one argument to log")
        ty = self.codeGen.typer.inferType(node.args[0])
        v = self.codeGen.visit(node.args[0])
        if(ty==int):
            l = self.codeGen.builder.sitofp(v, llFloatType)
            return self.codeGen.builder.fptosi(self.codeGen.builder.call(self.codeGen._flog, [l]),  llIntType)
        elif(ty==float):
            return self.codeGen.builder.call(self.codeGen._flog, [v])
        raise PyllvmError("mmath: unhandled type for log") 
    
    def emitexp(self, node):
        if(len(node.args)!=1):
            raise PyllvmError("mmath: one argument to log")
        ty = self.codeGen.typer.inferType(node.args[0])
        v = self.codeGen.visit(node.args[0])
        if(ty==int):
            l = self.codeGen.builder.sitofp(v, llFloatType)
            return self.codeGen.builder.fptosi(self.codeGen.builder.call(self.codeGen._exp, [l]),  llIntType)
        elif(ty==float):
            return self.codeGen.builder.call(self.codeGen._exp, [v])
        raise PyllvmError("mmath: unhandled type for log") 
    
    def emitsqrt(self, node):
        if(len(node.args)!=1):
            raise PyllvmError("mmath: one argument to sqrt")
        ty = self.codeGen.typer.inferType(node.args[0])
        v = self.codeGen.visit(node.args[0])
        if(ty==int):
            # first cast int to float, then do float sqrt
            i2f = self.codeGen.builder.sitofp(v, llFloatType, 'i2f')
            ret = self.codeGen.builder.call(self.codeGen._fsqrt, [i2f])
            return self.codeGen.builder.fptosi(ret, llIntType)
        elif(ty==float):
            return self.codeGen.builder.call(self.codeGen._fsqrt, [v])
        raise PyllvmError("mmath: unhandled type for sqrt") 
        
    def emitint(self, node):
        if(len(node.args)!=1):
            raise PyllvmError("mmath: one argument to int")
        ty = self.codeGen.typer.inferType(node.args[0])
        v = self.codeGen.visit(node.args[0])
        if(ty==int):
            return v
        elif(ty==float):
            return self.codeGen.builder.fptosi(v, llIntType)
        raise PyllvmError("mmath: unhandled type for int") 
    def emitfloat(self, node):
        if(len(node.args)!=1):
            raise PyllvmError("mmath: one argument to float")
        ty = self.codeGen.typer.inferType(node.args[0])
        v = self.codeGen.visit(node.args[0])
        if(ty==float):
            return v
        elif(ty==int):
            return self.codeGen.builder.sitofp(v, llFloatType)
        raise PyllvmError("mmath: unhandled type for float") 

    # NOTE: need to pass constants because creating array from dims
    def emitrange(self, node):
        # get start and end points
        ty = self.codeGen.typer.inferType(node.args[0])
        if(ty!=int and ty!= float):
            raise PyllvmError("mmath: range needs numerical arguments")
        for n in node.args:
            if not isinstance(n, compiler.ast.Const):
                raise PyllvmError("mmath: need to pass range constant values")
        
        if len(node.args) == 1:
            start = 0
            end = int(node.args[0].value)
        else:
            start = int(node.args[0].value)
            end = int(node.args[1].value)

        if(end<start):
            raise PyllvmError("mmath: bad range args")
        # malloc array
        if(ty==int):
            arrTy = llvm.core.Type.array(llIntType, end-start)
        else:
            arrTy = llvm.core.Type.array(llFloatType, end-start)
        m_ptr = self.codeGen.builder.alloca_array(arrTy, llvm.core.Constant.int(llIntType, end-start))
            
        # copy all the values from the stack one into the heap
        zero = llvm.core.Constant.int(llIntType, 0)
        count = 0
        for v in range(start, end+1):
            index = llvm.core.Constant.int(llIntType, count)
            # create value to store
            if ty==int:
                val = llvm.core.Constant.int(llIntType, v)
            else:
                val = llvm.core.Constant.real(llFloatType, float(v))
            # store values in malloc'd array
            m = self.codeGen.builder.gep(m_ptr, [zero, index])
            self.codeGen.builder.store(val, m)
            count = count+1
        # reset expr to the malloc'd array ptr
        return m_ptr
    def emitzeros(self, node):
        # get start and end points
        ty = self.codeGen.typer.inferType(node.args[0])
        if(ty!=int and ty!= float):
            raise PyllvmError("mmath: zeros needs numerical arguments")
        for n in node.args:
            if not isinstance(n, compiler.ast.Const):
                raise PyllvmError("mmath: need to pass zeros constant values")
        if len(node.args) == 1:
            start = 0
            end = int(node.args[0].value)
            z = 0
        else:
            start = 0
            end = int(node.args[0].value)
            z = node.args[1].value
            ty = self.codeGen.typer.inferType(node.args[1])

        if(end<start):
            raise PyllvmError("mmath: bad zeros args")
        
        # malloc array
        if(ty==int):
            arrTy = llvm.core.Type.array(llIntType, end-start)
        else:
            arrTy = llvm.core.Type.array(llFloatType, end-start)
        m_ptr = self.codeGen.builder.alloca_array(arrTy, llvm.core.Constant.int(llIntType, end-start))
        # copy all the values from the stack one into the heap
        zero = llvm.core.Constant.int(llIntType, 0)
        count = 0
        for v in range(start, end+1):
            index = llvm.core.Constant.int(llIntType, count)
            # create value to store
            if ty==int:
                val = llvm.core.Constant.int(llIntType, z)
            else:
                val = llvm.core.Constant.real(llFloatType, z)
            # store values in malloc'd array
            m = self.codeGen.builder.gep(m_ptr, [zero, index])
            self.codeGen.builder.store(val, m)
            count = count+1
        # reset expr to the malloc'd array ptr
        return m_ptr

def isIntrinsicMathFunction(func):
    return intrinsics.has_key(func)
       
def GetIntrinsicMathFunctions():
    return intrinsics

