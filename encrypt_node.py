_A0='00000000-0000-0000-0000-000000000000'
_z='task_id'
_y='RiceRoundImageUrlNode'
_x='RiceRoundUploadImageNode'
_w='RiceRoundOutputImageBridgeNode'
_v='Node name for S&R'
_u='properties'
_t='RiceRoundEncryptNode'
_s='input_anything'
_r='main_link_type'
_q='last_node_id'
_p='owner_id'
_o='RiceRound'
_n='EXTRA_PNGINFO'
_m='PROMPT'
_l='UNIQUE_ID'
_k='template_id'
_j='hidden'
_i='optional'
_h='required'
_g='RiceRoundInputTextNode'
_f='class_type'
_e='main_link_id'
_d='slot_index'
_c='RiceRoundAdvancedChoiceNode'
_b='RiceRoundSimpleChoiceNode'
_a='RiceRoundDecryptNode'
_Z='extra_pnginfo'
_Y='prompt'
_X='RiceRoundStrToBooleanNode'
_W='RiceRoundBooleanNode'
_V='RiceRoundStrToFloatNode'
_U='RiceRoundStrToIntNode'
_T='RiceRoundFloatNode'
_S='RiceRoundIntNode'
_R='RiceRoundDownloadMaskNode'
_Q='RiceRoundMaskBridgeNode'
_P='RiceRoundImageBridgeNode'
_O='RiceRoundSimpleImageNode'
_N='name'
_M='unique_id'
_L='RiceRoundDownloadImageNode'
_K='IMAGE'
_J='default'
_I='inputs'
_H='STRING'
_G='label'
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
INPUT_NODE_TYPES=[_b,_c,_O,_L,_P,_g,_Q,_R,_S,_T,_U,_V,_W,_X]
class RiceRoundEncryptNode:
	def __init__(A):A.template_id=uuid.uuid4().hex
	@classmethod
	def INPUT_TYPES(A):return{_h:{'project_name':(_H,{_J:'my_project'}),_k:(_H,{_J:uuid.uuid4().hex})},_i:{'output':(_K,)},_j:{_M:_l,_Y:_m,_Z:_n}}
	@classmethod
	def IS_CHANGED(A,**B):return float('NaN')
	RETURN_TYPES=();OUTPUT_NODE=True;FUNCTION='encrypt';CATEGORY=_o
	def encrypt(E,project_name,template_id,output,**A):F=A.pop(_M,_B);B=A.pop(_Z,_B);C=A.pop(_Y,_B);D=Encrypt(B['workflow'],C,project_name,template_id);D.do_encrypt();return{}
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
				for B in E:B=int(B);A.link_owner_map[B][_D]=copy.deepcopy(E);A.link_owner_map[B][_d]=D.get(_d,0);A.link_owner_map[B][_p]=int(F[_C]);A.link_owner_map[B][_A]=D.get(_A,'')
		A.last_node_id=int(C[_q]);A.last_link_id=int(C['last_link_id'])
	def load_prompt(A):B=copy.deepcopy(A.original_prompt);A.node_prompt_map={int(A):B for(A,B)in B.items()}
	def analyze_input_from_workflow(A):
		for(id,B)in A.workflow_nodes_dict.items():
			E=B.get(_A,'')
			if E in INPUT_NODE_TYPES:
				A.input_node_map[id]=copy.deepcopy(B);C=B.get(_F,[])
				if not C:continue
				D=C[0].get(_D,[])
				if not D:continue
				F=int(D[0]);A.input_node_map[id][_e]=F;A.input_node_map[id][_r]=C[0].get(_A,_H)
	def assemble_new_workflow(A):C=list(A.input_node_map.keys());B=copy.deepcopy(A.original_workflow);A.related_node_ids=A.find_workflow_related_nodes(B[_D],C);B[_E]=[B for B in B[_E]if int(B[_C])in A.related_node_ids];A.invalid_new_workflow(B);D=A.add_decrypt_node(B);A.remove_redundant_links(B);A.remove_unrelated_nodes(B,A.related_node_ids,D);A.replace_choice_template(B);A.replace_workflow_node(B);A.output_file(B,f"workflow")
	def output_template_json_file(G):
		U='模型选择';T='提示词';S='请上传蒙版';R='image/*';Q='tip';P='max_size';O='accept';N='请上传图片';L='number';K='max';J='min';I='数值';F='settings';E='describe';V=RicePromptInfo();M=[]
		for(H,W)in G.input_node_map.items():
			X=W[_s];C=G.workflow_nodes_dict[H][_A];D=G.node_prompt_map[H].get(_I,{});A=str(D.get(_N,''));B={_C:str(X),_A:'',E:'输入组件','node_id':str(H),F:{}}
			if C in[_O,_L,_P]:B[_A]='image_upload';B[E]=A if A else N,;B[F]={_G:A if A else N,O:R,P:500000,Q:'请上传不超过500KB的图片'}
			elif C in[_Q,_R]:B[_A]='mask_upload';B[E]=A if A else S,;B[F]={_G:A if A else S,O:R,P:50000,Q:'请上传不超过50KB的图片'}
			elif C==_g:B[_A]='text';B[E]=A if A else T,;B[F]={_G:A if A else T,'placeholder':'请描述图片内容','multiline':True}
			elif C==_c or C==_b:B[_A]='choice';B[E]=A if A else U,;B[F]={_G:A if A else U,'options':V.get_choice_value(H),_J:D.get(_J,'')}
			elif C==_S or C==_U:B[_A]='number_int';B[E]=A if A else I,;B[F]={_G:A if A else I,J:D.get(J,0),K:D.get(K,1000),L:D.get(L,0)}
			elif C==_T or C==_V:B[_A]='number_float';B[E]=A if A else I,;B[F]={_G:A if A else I,J:D.get(J,.0),K:D.get(K,1e3),L:D.get(L,.0)}
			elif C==_W or C==_X:B[_A]='switch';B[E]=A if A else'开关';B[F]={_G:A if A else'开关',_J:D.get('value',False)}
			else:raise ValueError(f"Error: The node {H} is not a valid RiceRound node.")
			M.append(B)
		Y={_k:G.template_id,'title':G.project_name,'elements':M};G.output_file(Y,f"{G.template_id}_template")
	def assemble_new_prompt(A):'\n        组装新的prompt配置。主要完成:\n        1. 移除不需要的节点\n        2. 转换特定节点的类型和输入\n        3. 保存处理后的prompt配置\n        ';B=A._create_filtered_prompt();A._transform_node_types(B);A.output_file(B,f"{A.template_id}_job")
	def _create_filtered_prompt(B):
		'\n        创建经过过滤的prompt副本，移除不需要的节点\n        ';A=copy.deepcopy(B.original_prompt);C=B._get_exclude_node_ids(A)
		for D in C:A.pop(str(D),_B)
		return A
	def save_rice_zip(A):
		'\n        将工作流相关文件打包成rice.zip\n        包括:\n        - workflow.json\n        - {template_id}_job.json\n        - {template_id}_template.json \n        - choice_node文件夹(如果存在)\n        - original_workflow.json\n        - original_prompt.json\n        ';J='job.bin';import pyzipper as F
		try:
			C=[];B=[];G=[];D=os.path.join(A.project_folder,J)
			for K in[f"{A.template_id}_job.json",'original_workflow.json','original_prompt.json']:H=os.path.join(A.project_folder,K);G.append(H);B.append(H)
			combine_files(G,A.template_id,D);C.append((D,J));B.append(D);I=os.path.join(A.project_folder,f"{A.template_id}_template.json");C.append((I,'template.bin'));B.append(I);L=os.path.join(A.project_folder,'rice.zip')
			with F.AESZipFile(L,'w',compression=F.ZIP_DEFLATED)as M:
				for(E,N)in C:M.write(E,N)
			print(f"save zip success")
			for E in B:os.remove(E)
		except Exception as O:print(f"Error creating zip: {str(O)}");raise
	def _get_exclude_node_ids(A,prompt):
		'\n        获取需要从prompt中排除的节点ID集合\n        ';C={_t,_a,'RiceRoundDebugNode'};B=A.related_node_ids.difference(set(A.input_node_map.keys()))
		for(D,E)in prompt.items():
			if E.get(_f,'')in C:B.add(int(D))
		return B
	def _transform_node_types(K,prompt):
		'\n        转换节点类型和更新节点输入配置\n        ';J='image_url';D='str';B='new_inputs';A='new_type';E={_P:{A:_L,B:{J:''}},_O:{A:_L,B:{J:''}},_Q:{A:_R,B:{'mask_url':''}},_S:{A:_U,B:{D:''}},_T:{A:_V,B:{D:''}},_W:{A:_X,B:{D:''}}}
		for(L,C)in prompt.items():
			C.pop('is_changed',_B);F=C.get(_f,'');G=C.get(_I,{})
			if not G:continue
			H=G.get(_N,'')
			if F in E:
				I=E[F];C[_f]=I[A];C[_I]=I[B].copy()
				if H:C[_I][_N]=H
	def add_decrypt_node(A,workflow):
		C=workflow;G=set();A.last_node_id+=1;H={_C:A.last_node_id,_A:_a,'pos':[420,0],'size':[500,150],'flags':{},'mode':0,'order':20,_I:[],_F:[{_N:_K,_A:_K,_D:[],_G:_K,_d:0}],_u:{_v:_a},'widgets_values':[str(A.template_id)]}
		for(B,(D,E))in enumerate(A.input_node_map.items()):
			I=E[_e];F=E[_r];E[_s]=B;J={_N:f"input_anything{B if B>0 else''} ({D})",_A:'*','link':I,_G:f"input_anything{B if B>0 else''} ({D})"}
			if B==0:J['shape']=7
			H[_I].append(J)
			if F not in[_K,_H]:F=_H
			K=[I,D,0,A.last_node_id,B,F];C[_D].append(K)
		G.add(A.last_node_id);C[_E].append(H);C[_q]=A.last_node_id;return G
	def output_file(A,workflow,prefix):
		B=os.path.join(A.project_folder,f"{prefix}.json")
		with open(B,'w',encoding='utf-8')as C:json.dump(workflow,C,ensure_ascii=False,indent=4)
	def remove_redundant_links(D,workflow):
		B=workflow;E=set()
		for C in B[_E]:
			F=int(C[_C])
			if F in D.input_node_map:
				G=D.input_node_map[F][_e];A=C.get(_F,[])
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
			if A.get(_A,'')==_c:
				F=E.get_choice_classname(B)
				if F:A[_A]=F
				else:print(f"Warning: The node {B} is not a valid RiceRound Choice node.")
		G={}
		for(B,A)in H.input_node_map.items():
			if A.get(_A,'')==_b:I=E.get_choice_value(B);G[B]=I
		if D not in C:C[D]={}
		C[D]['choice_node_map']=G
	def replace_workflow_node(J,workflow):
		I='unknown';D=workflow;C='RiceRoundOutputTextNode';E={_P:_w,_O:_x,_L:_y,_Q:'RiceRoundOutputMaskBridgeNode',_R:'RiceRoundMaskUrlNode',_S:'RiceRoundOutputIntNode',_T:'RiceRoundOutputFloatNode',_W:'RiceRoundOutputBooleanNode',_X:C,_U:C,_V:C};F=set()
		for A in D[_E]:
			G=A.get(_A,'')
			if G in E:
				if _F not in A:raise ValueError(f"Node {A.get(_C,I)} missing outputs")
				if not A[_F]or not isinstance(A[_F],list):raise ValueError(f"Invalid outputs format in node {A.get(_C,I)}")
				H=E[G];A.update({_A:H,_F:[{_A:_H,**A[_F][0]}],_u:{_v:H}});F.add(int(A[_C]))
		for B in D[_D]:
			if len(B)==6 and B[1]in F:B[5]=_H
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
			elif B==_t:D+=1;continue
			if B in[_a,_w,_x,_y]:raise ValueError(f"Error: The node {A[_C]} is not a valid RiceRound node.")
		if D!=1:raise ValueError('Error: Multiple RiceRoundEncryptNode nodes are not allowed.')
		if C is _B:raise ValueError("Error: The node is not an 'RiceRoundOutputImageNode'.")
	def invalid_new_workflow(A,workflow):
		for B in workflow[_E]:
			C=B.get(_I,[])
			for input in C:
				D=int(input.get('link',0));E=A.link_owner_map[D][_p];F=A.workflow_nodes_dict[E][_A]
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
	def INPUT_TYPES(A):return{_h:{'images':(_K,)},_i:{_z:(_H,{_J:_A0})},_j:{_M:_l,_Y:_m,_Z:_n}}
	RETURN_TYPES=();OUTPUT_NODE=True;FUNCTION='load';CATEGORY=_o
	def load(S,images,task_id,**C):
		L='image_type';E='PNG';B=task_id;A=images;F=C.pop(_M,_B);M=C.pop(_Y,_B);T=C.pop(_Z,_B);G=PromptServer.instance.client_id;H=''
		if hasattr(PromptServer.instance,'last_prompt_id')and PromptServer.instance.last_prompt_id:H=PromptServer.instance.last_prompt_id
		if F is _B:raise Exception("Warning: 'unique_id' is missing.")
		if M is _B:raise Exception("Warning: 'prompt' is missing.")
		if B==_A0 or B=='':
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
			Q={L:E,'image_results':J};R={_z:B,_M:F,'client_id':G,'prompt_id':H,'timestamp':int(time.time()*1000),L:E,'result_data':Q};PromptServer.instance.send_sync('rice_round_done',R,sid=G);return{}