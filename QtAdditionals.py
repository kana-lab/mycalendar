
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from inspect import isclass


_qt_additionals_pre_qwidget=QWidget

class RWidget(_qt_additionals_pre_qwidget):
	rpos=None
	
	def setRPos(self,string):
		self.rpos=RPos(string)
	
	def resizeEvent(self,e):
		_qt_additionals_pre_qwidget.resizeEvent(self,e)
		for obj in self.children():
			if isinstance(obj,RWidget) and obj.rpos is not None:
				obj.setGeometry(*obj.rpos.geometry(e.size()))
		self.r_resized(self.size())
	
	def r_resized(self,e):
		pass

def _qt_additionals_init(v):
	global QWidget
	v=v.copy()
	for key,item in v.items():
		if isclass(item) and QWidget in item.__bases__:
			if item==RWidget: continue
			ls=list(item.__bases__)
			ls[ls.index(QWidget)]=RWidget
			item.__bases__=tuple(ls)
	QWidget=RWidget
_qt_additionals_init(vars())


''' # monkey-patch such as below doesn't work.
def _qt_additionals_init():
	QWidget.rpos=None
	
	def setRPos(self,string): self.rpos=RPos(string)
	def postResizeEvent(self,e): pass
	
	QWidget.setRPos=setRPos
	QWidget.postResizeEvent=postResizeEvent
	old_resizeEvent=QWidget.resizeEvent
	
	def resizeEvent(self,e):
		print('called')
		old_resizeEvent(self,e)
		for obj in self.children():
			if isinstance(obj,QWidget) and obj.rpos is not None:
				obj.setGeometry(*obj.rpos.geometry(e.size()))
		self.postResizeEvent(self.size())
	
	QWidget.resizeEvent=resizeEvent
_qt_additionals_init()
'''


class _Order:
	def __init__(self):
		self.kind=None
		self.dollar=False
		self.n=None
		self.percent=False
		self.suffix=None 
	
	def __call__(self,x:QSize):
		base=x.width() if self.kind in 'xw' else x.height()
		origin=0 if not self.dollar else base
		val=self.n if not self.percent else base*self.n//100
		return origin+val


class RPos:
	def __init__(self,expressions):
		self.container=[]
		self.geometry=None
		self.lexer(expressions)
		self.parser()
	
	def lexer(self,expressions):
		self.container=[]
		e=''.join(expressions.split())
		while True:
			s=_Order()
			self.container.append(s)
			
			if len(e)<3:
				raise Exception(f'invalid characters: {e}')
			
			if e[0] not in 'xywh':
				raise Exception(f'invalid kind of position: {e[0]}')
			s.kind=e[0]
			
			if e[1]!=':':
				raise Exception(f'colon is needed before \'{e[1]}\'')
			
			if e[2]=='$':
				if s.kind in 'wh':
					raise Exception('can\'t use \'$\' expression with type w/h')
				s.dollar=True
				e=e[3:]
			else:
				s.dollar=False
				e=e[2:]
			if not e:
				raise Exception('no value is given')
			
			for i in range(len(e)):
				if e[i] not in '1234567890-+':
					break
			else:
				i+=1
			s.n=int(e[:i])
			e=e[i:]
			
			if e:
				if e[0]=='%':
					s.percent=True
					e=e[1:]
				else:
					s.percent=False
			
			if s.kind in 'xy':
				if not e:
					raise Exception('the position which has x/y kind must have suffix.')
				if e[0] not in 'tcb':
					raise Exception(f'invalid suffix: {e[0]}')
				s.suffix=e[0]
				e=e[1:]
			
			if not e:
				break
			else:
				if e[0]!=',':
					raise Exception(f'\',\' is needed before \'{e[0]}\'')
				e=e[1:]
	
	def parser(self):
		dc={'t':0, 'c':1/2, 'b':1}
		
		xs, ys=[], []
		for s in self.container:
			if s.kind in 'xw':
				xs.append(s)
			else:
				ys.append(s)
		
		if len(xs)!=2 or len(ys)!=2:
			raise Exception('invalid geometry specification')
		
		if xs[0].kind=='w' or xs[1].kind=='w':
			width, x=(xs[0], xs[1]) if xs[0].kind=='w' else (xs[1], xs[0])
			if x.kind!='x':
				raise Exception('invalid width assignment')
			kx=dc[x.suffix]
			left=lambda size: (x(size)-int(kx*width(size)))
		else:
			if xs[0].suffix==xs[1].suffix:
				raise Exception('invalid specification of x')
			xs.sort(key=lambda s: dc[s.suffix])
			k=dc[xs[1].suffix]-dc[xs[0].suffix]
			width=lambda size: int((xs[1](size)-xs[0](size))/k)
			left=xs[0] if xs[0].suffix=='t' else lambda size: 2*xs[0](size)-xs[1](size)
		
		if ys[0].kind=='h' or ys[1].kind=='h':
			height, y=(ys[0], ys[1]) if ys[0].kind=='h' else (ys[1], ys[0])
			if y.kind!='y':
				raise Exception('invalid height assignment')
			k=dc[y.suffix]
			top=lambda size: y(size)-int(k*height(size))
		else:
			if ys[0].suffix==ys[1].suffix:
				raise Exception('invalid specification of y')
			ys.sort(key=lambda s: dc[s.suffix])
			ky=dc[ys[1].suffix]-dc[ys[0].suffix]
			height=lambda size: int((ys[1](size)-ys[0](size))/ky)
			top=ys[0] if ys[0].suffix=='t' else lambda size: 2*ys[0](size)-ys[1](size)
		
		self.geometry=lambda size: (left(size),top(size),width(size),height(size))


