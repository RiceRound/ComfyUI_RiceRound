_z='00000000-0000-0000-0000-000000000000'
_y='task_id'
_x='RiceRoundImageUrlNode'
_w='RiceRoundUploadImageNode'
_v='RiceRoundOutputImageBridgeNode'
_u='Node name for S&R'
_t='properties'
_s='RiceRoundEncryptNode'
_r='input_anything'
_q='main_link_type'
_p='last_node_id'
_o='owner_id'
_n='RiceRound'
_m='EXTRA_PNGINFO'
_l='PROMPT'
_k='UNIQUE_ID'
_j='template_id'
_i='hidden'
_h='optional'
_g='required'
_f='RiceRoundInputTextNode'
_e='class_type'
_d='main_link_id'
_c='slot_index'
_b='RiceRoundAdvancedChoiceNode'
_a='RiceRoundSimpleChoiceNode'
_Z='RiceRoundDecryptNode'
_Y='extra_pnginfo'
_X='prompt'
_W='RiceRoundStrToBooleanNode'
_V='RiceRoundBooleanNode'
_U='RiceRoundStrToFloatNode'
_T='RiceRoundStrToIntNode'
_S='RiceRoundFloatNode'
_R='RiceRoundIntNode'
_Q='RiceRoundDownloadMaskNode'
_P='RiceRoundMaskBridgeNode'
_O='RiceRoundImageBridgeNode'
_N='RiceRoundSimpleImageNode'
_M='name'
_L='unique_id'
_K='RiceRoundDownloadImageNode'
_J='IMAGE'
_I='default'
_H='inputs'
_G='STRING'
_F='outputs'
_E='nodes'
_D='links'
_C='id'
_B=None
_A='type'
from collections import defaultdict
import copy
from io import BytesIO
import json,os,uuid,numpy as np,comfy.utils,time
from PIL import Image
from.utils import combine_files
from.rice_url_config import machine_upload_image
if __name__=='__main__':output_project_folder='D:\\output'
else:import folder_paths;from server import PromptServer;from.rice_url_config import RiceUrlConfig;from.rice_prompt_info import RicePromptInfo;output_project_folder=folder_paths.output_directory
INPUT_NODE_TYPES=[_a,_b,_N,_K,_O,_f,_P,_Q,_R,_S,_T,_U,_V,_W]
class RiceRoundEncryptNode:
	def __init__(A):A.template_id=uuid.uuid4().hex
	@classmethod
	def INPUT_TYPES(A):return{_g:{'project_name':(_G,{_I:'my_project'}),_j:(_G,{_I:uuid.uuid4().hex})},_h:{'output':(_J,)},_i:{_L:_k,_X:_l,_Y:_m}}
	@classmethod
	def IS_CHANGED(A,**B):return float('NaN')
	RETURN_TYPES=();OUTPUT_NODE=True;FUNCTION='encrypt';CATEGORY=_n
	def encrypt(E,project_name,template_id,output,**A):F=A.pop(_L,_B);B=A.pop(_Y,_B);C=A.pop(_X,_B);D=Encrypt(B['workflow'],C,project_name,template_id);D.do_encrypt();return{}
class Encrypt:
	def __init__(A,workflow,prompt,project_name,template_id):
		A.original_workflow=workflow;A.original_prompt=prompt;A.template_id=template_id;A.project_name=project_name;A.project_folder=os.path.join(output_project_folder,A.project_name)
		if not os.path.exists(A.project_folder):os.makedirs(A.project_folder)
		A.last_node_id=0;A.last_link_id=0;A.link_owner_map=defaultdict(dict);A.workflow_nodes_dict={};A.node_prompt_map={};A.input_node_map={};A.related_node_ids=set()
	def do_encrypt(A):A.invalid_workflow(A.original_workflow);A.load_workflow();A.load_prompt();A.analyze_input_from_workflow();A.assemble_new_workflow();A.output_template_json_file();A.assemble_new_prompt();RicePromptInfo().save_choice_classname(A.project_folder);A.output_file(A.original_workflow,f"original_workflow");A.output_file(A.original_prompt,f"original_prompt");A.save_rice_zip();A.clear()
	def clear(A):A.original_workflow=_B;A.original_prompt=_B;A.template_id=_B;A.project_name=_B;A.project_folder=_B;A.last_node_id=0;A.last_link_id=0;RicePromptInfo().clear()
	def load_workflow(A):
		C=copy.deepcopy(A.original_workflow);A.workflow_nodes_dict={int(A[_C]):A for A in C[_E]}
		for F in C[_E]:
			G=F.get(_F,[])
			if not G:continue
			for D in G:
				E=D.get(_D,[])
				if not E:continue
				for B in E:B=int(B);A.link_owner_map[B][_D]=copy.deepcopy(E);A.link_owner_map[B][_c]=D.get(_c,0);A.link_owner_map[B][_o]=int(F[_C]);A.link_owner_map[B][_A]=D.get(_A,'')
		A.last_node_id=int(C[_p]);A.last_link_id=int(C['last_link_id'])
	def load_prompt(A):B=copy.deepcopy(A.original_prompt);A.node_prompt_map={int(A):B for(A,B)in B.items()}
	def analyze_input_from_workflow(A):
		for(id,B)in A.workflow_nodes_dict.items():
			E=B.get(_A,'')
			if E in INPUT_NODE_TYPES:
				A.input_node_map[id]=copy.deepcopy(B);C=B.get(_F,[])
				if not C:continue
				D=C[0].get(_D,[])
				if not D:continue
				F=int(D[0]);A.input_node_map[id][_d]=F;A.input_node_map[id][_q]=C[0].get(_A,_G)
		A.input_node_map={A:B for(A,B)in sorted(A.input_node_map.items(),key=lambda x:x[0])}
	def assemble_new_workflow(A):C=list(A.input_node_map.keys());B=copy.deepcopy(A.original_workflow);A.related_node_ids=A.find_workflow_related_nodes(B[_D],C);B[_E]=[B for B in B[_E]if int(B[_C])in A.related_node_ids];A.invalid_new_workflow(B);D=A.add_decrypt_node(B);A.remove_redundant_links(B);A.remove_unrelated_nodes(B,A.related_node_ids,D);A.replace_choice_template(B);A.replace_workflow_node(B);A.output_file(B,f"workflow")
	def output_template_json_file(F):
		P='image/*';O='tip';N='max_size';M='accept';J='number';I='max';H='min';E='settings';D='describe';Q=RicePromptInfo();K=[]
		for(G,R)in F.input_node_map.items():
			S=R[_r];B=F.workflow_nodes_dict[G][_A];C=F.node_prompt_map[G].get(_H,{});L=str(C.get(_M,''));A={_C:str(S),_A:'',D:'输入组件','node_id':str(G),E:{}}
			if B in[_N,_K,_O]:A[_A]='image_upload';A[D]='请上传图片';A[E]={M:P,N:500000,O:'请上传不超过500KB的图片'}
			elif B in[_P,_Q]:A[_A]='mask_upload';A[D]='请上传蒙版';A[E]={M:P,N:50000,O:'请上传不超过50KB的图片'}
			elif B==_f:A[_A]='text';A[D]='提示词';A[E]={'placeholder':'请描述图片内容','multiline':True}
			elif B==_b or B==_a:A[_A]='choice';A[D]='模型选择';A[E]={'options':Q.get_choice_value(G),_I:C.get(_I,'')}
			elif B==_R or B==_T:A[_A]='number_int';A[D]='数值';A[E]={H:C.get(H,0),I:C.get(I,1000),J:C.get(J,0)}
			elif B==_S or B==_U:A[_A]='number_float';A[D]='数值';A[E]={H:C.get(H,.0),I:C.get(I,1e3),J:C.get(J,.0)}
			elif B==_V or B==_W:A[_A]='switch';A[D]='开关';A[E]={_I:C.get('value',False)}
			else:raise ValueError(f"Error: The node {G} is not a valid RiceRound node.")
			if L:A[D]=L
			K.append(A)
		T={_j:F.template_id,'title':F.project_name,'elements':K};F.output_file(T,f"{F.template_id}_template")
	def assemble_new_prompt(A):'\n        组装新的prompt配置。主要完成:\n        1. 移除不需要的节点\n        2. 转换特定节点的类型和输入\n        3. 保存处理后的prompt配置\n        ';B=A._create_filtered_prompt();A._transform_node_types(B);A.output_file(B,f"{A.template_id}_job")
	def _create_filtered_prompt(B):
		'\n        创建经过过滤的prompt副本，移除不需要的节点\n        ';A=copy.deepcopy(B.original_prompt);C=B._get_exclude_node_ids(A)
		for D in C:A.pop(str(D),_B)
		return A
	def save_rice_zip(A):
		'\n        将工作流相关文件打包成rice.zip\n        包括:\n        - workflow.json\n        - {template_id}_job.json\n        - {template_id}_template.json \n        - choice_node文件夹(如果存在)\n        - original_workflow.json\n        - original_prompt.json\n        ';I='job.bin';import pyzipper as F
		try:
			B=[];C=[];G=[];D=os.path.join(A.project_folder,I)
			for J in[f"{A.template_id}_job.json",'original_workflow.json','original_prompt.json']:H=os.path.join(A.project_folder,J);G.append(H);C.append(H)
			combine_files(G,A.template_id,D);B.append((D,I));C.append(D);K=os.path.join(A.project_folder,f"{A.template_id}_template.json");B.append((K,'template.bin'));L=os.path.join(A.project_folder,'rice.zip')
			with F.AESZipFile(L,'w',compression=F.ZIP_DEFLATED)as M:
				for(E,N)in B:M.write(E,N)
			print(f"save zip success")
			for E in C:os.remove(E)
		except Exception as O:print(f"Error creating zip: {str(O)}");raise
	def _get_exclude_node_ids(A,prompt):
		'\n        获取需要从prompt中排除的节点ID集合\n        ';C={_s,_Z,'RiceRoundDebugNode'};B=A.related_node_ids.difference(set(A.input_node_map.keys()))
		for(D,E)in prompt.items():
			if E.get(_e,'')in C:B.add(int(D))
		return B
	def _transform_node_types(K,prompt):
		'\n        转换节点类型和更新节点输入配置\n        ';J='image_url';D='str';B='new_inputs';A='new_type';E={_O:{A:_K,B:{J:''}},_N:{A:_K,B:{J:''}},_P:{A:_Q,B:{'mask_url':''}},_R:{A:_T,B:{D:''}},_S:{A:_U,B:{D:''}},_V:{A:_W,B:{D:''}}}
		for(L,C)in prompt.items():
			C.pop('is_changed',_B);F=C.get(_e,'');G=C.get(_H,{})
			if not G:continue
			H=G.get(_M,'')
			if F in E:
				I=E[F];C[_e]=I[A];C[_H]=I[B].copy()
				if H:C[_H][_M]=H
	def add_decrypt_node(A,workflow):
		K='label';C=workflow;G=set();A.last_node_id+=1;H={_C:A.last_node_id,_A:_Z,'pos':[420,0],'size':[500,150],'flags':{},'mode':0,'order':20,_H:[],_F:[{_M:_J,_A:_J,_D:[],K:_J,_c:0}],_t:{_u:_Z},'widgets_values':[str(A.template_id),735127949069071,'randomize']}
		for(B,(D,E))in enumerate(A.input_node_map.items()):
			I=E[_d];F=E[_q];E[_r]=B;J={_M:f"input_anything{B if B>0 else''} ({D})",_A:'*','link':I,K:f"input_anything{B if B>0 else''} ({D})"}
			if B==0:J['shape']=7
			H[_H].append(J)
			if F not in[_J,_G]:F=_G
			L=[I,D,0,A.last_node_id,B,F];C[_D].append(L)
		G.add(A.last_node_id);C[_E].append(H);C[_p]=A.last_node_id;return G
	def output_file(A,workflow,prefix):
		B=os.path.join(A.project_folder,f"{prefix}.json")
		with open(B,'w',encoding='utf-8')as C:json.dump(workflow,C,ensure_ascii=False,indent=4)
	def remove_redundant_links(D,workflow):
		B=workflow;E=set()
		for C in B[_E]:
			F=int(C[_C])
			if F in D.input_node_map:
				G=D.input_node_map[F][_d];A=C.get(_F,[])
				if not A:continue
				if len(A)!=1:raise ValueError(f"Error: The node {C[_C]} has an invalid number of outputs.")
				H=A[0].get(_D,[])
				if not H:continue
				for I in H:
					if I!=G:E.add(I)
				A[0][_D]=[G]
		B[_D]=[A for A in B[_D]if isinstance(A,list)and len(A)==6 and A[0]not in E]
	def replace_choice_template(H,workflow):
		D='extra';C=workflow;E=RicePromptInfo()
		for A in C[_E]:
			B=int(A[_C])
			if A.get(_A,'')==_b:
				F=E.get_choice_classname(B)
				if F:A[_A]=F
				else:print(f"Warning: The node {B} is not a valid RiceRound Choice node.")
		G={}
		for(B,A)in H.input_node_map.items():
			if A.get(_A,'')==_a:I=E.get_choice_value(B);G[B]=I
		if D not in C:C[D]={}
		C[D]['choice_node_map']=G
	def replace_workflow_node(J,workflow):
		I='unknown';D=workflow;C='RiceRoundOutputTextNode';E={_O:_v,_N:_w,_K:_x,_P:'RiceRoundOutputMaskBridgeNode',_Q:'RiceRoundMaskUrlNode',_R:'RiceRoundOutputIntNode',_S:'RiceRoundOutputFloatNode',_V:'RiceRoundOutputBooleanNode',_W:C,_T:C,_U:C};F=set()
		for A in D[_E]:
			G=A.get(_A,'')
			if G in E:
				if _F not in A:raise ValueError(f"Node {A.get(_C,I)} missing outputs")
				if not A[_F]or not isinstance(A[_F],list):raise ValueError(f"Invalid outputs format in node {A.get(_C,I)}")
				H=E[G];A.update({_A:H,_F:[{_A:_G,**A[_F][0]}],_t:{_u:H}});F.add(int(A[_C]))
		for B in D[_D]:
			if len(B)==6 and B[1]in F:B[5]=_G
	def remove_unrelated_nodes(E,workflow,related_node_ids,new_node_ids):
		B=workflow;C=[];D=related_node_ids.union(new_node_ids)
		for A in B[_D]:
			if len(A)==6:
				if A[1]in D and A[3]in D:C.append(A)
		B[_D]=C
	@staticmethod
	def invalid_workflow(workflow):
		C=_B;D=0
		for A in workflow[_E]:
			B=A.get(_A,'')
			if B=='RiceRoundOutputImageNode':C=A;continue
			elif B==_s:D+=1;continue
			if B in[_Z,_v,_w,_x]:raise ValueError(f"Error: The node {A[_C]} is not a valid RiceRound node.")
		if D!=1:raise ValueError('Error: Multiple RiceRoundEncryptNode nodes are not allowed.')
		if C is _B:raise ValueError("Error: The node is not an 'RiceRoundOutputImageNode'.")
	def invalid_new_workflow(A,workflow):
		for B in workflow[_E]:
			C=B.get(_H,[])
			for input in C:
				D=int(input.get('link',0));E=A.link_owner_map[D][_o];F=A.workflow_nodes_dict[E][_A]
				if F in INPUT_NODE_TYPES:raise ValueError(f"Error: The node {B[_C]} may have circular references, generation failed.")
	def find_workflow_related_nodes(F,links,input_ids):
		E=input_ids;B=set(E);C=list(E)
		while C:
			G=C.pop()
			for D in links:
				if len(D)==6 and D[3]==G:
					A=D[1]
					if A not in B:
						if A in F.workflow_nodes_dict:B.add(A)
					C.append(A)
		return B
class RiceRoundOutputImageNode:
	def __init__(A):A.url_config=RiceUrlConfig()
	@classmethod
	def INPUT_TYPES(A):return{_g:{'images':(_J,)},_h:{_y:(_G,{_I:_z})},_i:{_L:_k,_X:_l,_Y:_m}}
	RETURN_TYPES=();OUTPUT_NODE=True;FUNCTION='load';CATEGORY=_n
	def load(S,images,task_id,**C):
		L='image_type';E='PNG';B=task_id;A=images;F=C.pop(_L,_B);M=C.pop(_X,_B);T=C.pop(_Y,_B);G=PromptServer.instance.client_id;H=''
		if hasattr(PromptServer.instance,'last_prompt_id')and PromptServer.instance.last_prompt_id:H=PromptServer.instance.last_prompt_id
		if F is _B:raise Exception("Warning: 'unique_id' is missing.")
		if M is _B:raise Exception("Warning: 'prompt' is missing.")
		if B==_z or B=='':
			N=comfy.utils.ProgressBar(A.shape[0]);I=0
			for D in A:O=255.*D.cpu().numpy();P=Image.fromarray(np.clip(O,0,255).astype(np.uint8));N.update_absolute(I,A.shape[0],(E,P,_B));I+=1
			return{}
		else:
			print(f"RiceRoundOutputImageNode task_id: {B}")
			if A.shape[0]>5:raise ValueError('Error: Cannot upload more than 5 images.')
			J=[]
			for D in A:
				K=machine_upload_image(D,B)
				if not K:raise ValueError('Error: Failed to upload image.')
				J.append(K)
			Q={L:E,'image_results':J};R={_y:B,_L:F,'client_id':G,'prompt_id':H,'timestamp':int(time.time()*1000),L:E,'result_data':Q};PromptServer.instance.send_sync('rice_round_done',R,sid=G);return{}