const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const state = { token: localStorage.getItem('pe-token'), user: null, data: {}, transactionLines: [] };
const titles = { dashboard:'Resumen', sales:'Nueva venta', purchases:'Nueva compra', returns:'Devolución de cliente', payments:'Abonos y cobranza', inventory:'Inventario de ediciones', publications:'Publicaciones', customers:'Clientes', suppliers:'Proveedores', routes:'Rutas de reparto', reports:'Movimientos', users:'Usuarios' };
const money = n => new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN'}).format(n || 0);
const date = v => v ? new Intl.DateTimeFormat('es-MX',{dateStyle:'medium'}).format(new Date(v)) : '—';
const esc = v => String(v ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

async function api(path, options={}) {
  const response = await fetch('/api'+path,{...options,headers:{'Content-Type':'application/json',...(state.token?{Authorization:'Bearer '+state.token}:{}),...(options.headers||{})}});
  if(response.status===401 && path!='/auth/login'){ logout(); throw new Error('Tu sesión terminó'); }
  const body = response.status===204 ? null : await response.json().catch(()=>null);
  if(!response.ok) throw new Error(body?.error || (response.status===401?'Usuario o contraseña incorrectos':'No fue posible completar la operación'));
  return body;
}
function toast(message){ const el=$('#toast'); el.textContent=message; el.classList.add('show'); setTimeout(()=>el.classList.remove('show'),2800); }
function logout(){ localStorage.removeItem('pe-token'); state.token=null; state.user=null; $('#app').classList.add('hidden'); $('#login').classList.remove('hidden'); }

$('#login-form').addEventListener('submit', async e => {
  e.preventDefault(); $('#login-error').textContent='';
  try { const result=await api('/auth/login',{method:'POST',body:JSON.stringify({username:$('#login-user').value,password:$('#login-password').value})}); state.token=result.token;state.user=result.user;localStorage.setItem('pe-token',state.token);start(); }
  catch(err){ $('#login-error').textContent=err.message; }
});
$('#logout').onclick=async()=>{ try{await api('/auth/logout',{method:'POST'})}catch{} logout(); };
$('#menu-toggle').onclick=()=>$('.sidebar').classList.toggle('open');
$('#modal-close').onclick=$('#modal-cancel').onclick=()=>$('#modal').close();

async function start(){
  if(!state.user){ try{state.user=await api('/auth/me')}catch{return logout()} }
  $('#login').classList.add('hidden');$('#app').classList.remove('hidden');
  $('#user-name').textContent=state.user.displayName;$('#user-role').textContent=state.user.role==='Admin'?'Administrador':'Operador';
  $('#user-initials').textContent=state.user.displayName.split(' ').map(x=>x[0]).slice(0,2).join('').toUpperCase();
  $$('.admin-only').forEach(x=>x.style.display=state.user.role==='Admin'?'':'none');
  $('#today').textContent=new Intl.DateTimeFormat('es-MX',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date());
  await navigate('dashboard');
}
$$('#nav button').forEach(btn=>btn.onclick=()=>navigate(btn.dataset.view));
$('#quick-sale').onclick=()=>navigate('sales');

async function navigate(view){
  $$('#nav button').forEach(x=>x.classList.toggle('active',x.dataset.view===view));
  $('#page-title').textContent=titles[view];$('.sidebar').classList.remove('open');
  $('#content').innerHTML='<div class="empty">Cargando…</div>';
  try {
    if(view==='dashboard') await renderDashboard();
    else if(['customers','suppliers','publications','inventory','routes','users'].includes(view)) await renderCatalog(view);
    else if(['sales','purchases','returns'].includes(view)) await renderTransaction(view);
    else if(view==='payments') await renderPayments();
    else if(view==='reports') await renderReports();
  } catch(err){ $('#content').innerHTML=`<div class="panel empty">${esc(err.message)}</div>`; }
}

async function loadBase(force=false){
  if(force || !state.data.customers) {
    const [customers,suppliers,publications,editions,routes]=await Promise.all(['/customers','/suppliers','/publications','/editions','/routes'].map(api));
    Object.assign(state.data,{customers,suppliers,publications,editions,routes});
  }
  return state.data;
}
const customerName=id=>state.data.customers?.find(x=>x.id===id)?.name||'Mostrador';
const supplierName=id=>state.data.suppliers?.find(x=>x.id===id)?.name||'—';
const pubName=id=>state.data.publications?.find(x=>x.id===id)?.title||'—';
const editionName=id=>{const e=state.data.editions?.find(x=>x.id===id);return e?`${pubName(e.publicationId)} · ${e.number}`:'—'};

async function renderDashboard(){
  const d=await api('/dashboard');await loadBase(true);
  $('#content').innerHTML=`
    <div class="hero"><div><span class="eyebrow">PANORAMA DEL DÍA</span><h1>Todo bajo control</h1><p>Indicadores actualizados de la distribuidora.</p></div></div>
    <div class="cards">
      ${metric('Ventas de hoy',money(d.salesToday),'↗','Operación del día')}
      ${metric('Por cobrar',money(d.receivables),'$','Saldo de clientes')}
      ${metric('Inventario',d.inventoryUnits.toLocaleString('es-MX'),'▦',money(d.inventoryValue)+' en existencia')}
      ${metric('Clientes activos',d.activeCustomers,'◉',`${d.lowStock} ediciones con stock bajo`)}
    </div>
    <div class="grid-2"><div class="panel"><div class="panel-head"><h3>Actividad reciente</h3><button class="secondary" data-go="reports">Ver todo</button></div>${movementTable(d.recent)}</div>
    <div class="panel"><div class="panel-head"><h3>Atención de inventario</h3></div>${stockAlerts()}</div></div>`;
  $$('[data-go]').forEach(x=>x.onclick=()=>navigate(x.dataset.go));
}
function metric(label,value,icon,detail){return `<article class="metric"><div class="metric-head"><span>${label}</span><i>${icon}</i></div><strong>${value}</strong><small>${detail}</small></article>`}
function stockAlerts(){
  const low=state.data.editions.filter(x=>x.active&&x.stock<=8).sort((a,b)=>a.stock-b.stock).slice(0,6);
  if(!low.length)return '<div class="empty">Sin alertas de inventario</div>';
  const max=Math.max(...low.map(x=>x.stock),8);return low.map(x=>`<div class="progress-row"><span>${esc(editionName(x.id))}</span><b class="${x.stock<=3?'low':''}">${x.stock}</b><div class="progress"><span style="width:${Math.max(5,x.stock/max*100)}%"></span></div></div>`).join('');
}
function movementTable(items){
  if(!items?.length)return '<div class="empty">Aún no hay movimientos</div>';
  return `<div class="table-wrap"><table><thead><tr><th>Folio</th><th>Tipo</th><th>Fecha</th><th>Cliente / proveedor</th><th>Total</th></tr></thead><tbody>${items.map(x=>`<tr><td><b>${esc(x.folio)}</b></td><td><span class="badge ${x.type.toLowerCase()}">${{Sale:'Venta',Purchase:'Compra',Return:'Devolución'}[x.type]}</span></td><td>${date(x.createdAt)}</td><td>${esc(x.customerId?customerName(x.customerId):supplierName(x.supplierId))}</td><td><b>${money(x.total)}</b></td></tr>`).join('')}</tbody></table></div>`;
}

const catalogMeta={
  customers:{endpoint:'/customers',singular:'cliente',columns:[['code','Clave'],['name','Nombre'],['phone','Teléfono'],['city','Ciudad'],['creditLimit','Límite'],['balance','Saldo']],fields:[['code','Clave'],['name','Nombre','text',true],['rfc','RFC'],['phone','Teléfono'],['email','Correo','email'],['address','Dirección'],['city','Ciudad'],['creditLimit','Límite de crédito','number'],['discountPercent','Descuento %','number']]},
  suppliers:{endpoint:'/suppliers',singular:'proveedor',columns:[['code','Clave'],['name','Nombre'],['rfc','RFC'],['phone','Teléfono'],['email','Correo'],['balance','Saldo']],fields:[['code','Clave'],['name','Nombre','text',true],['rfc','RFC'],['phone','Teléfono'],['email','Correo','email'],['address','Dirección']]},
  publications:{endpoint:'/publications',singular:'publicación',columns:[['code','Clave'],['title','Título'],['supplierId','Proveedor'],['barcode','Código de barras'],['taxPercent','IVA %']],fields:[['code','Clave'],['title','Título','text',true],['supplierId','Proveedor','supplier',true],['barcode','Código de barras'],['taxPercent','IVA %','number'],['monitored','Monitoreada','checkbox']]},
  inventory:{endpoint:'/editions',singular:'edición',columns:[['publicationId','Publicación'],['number','Edición'],['barcode','Código de barras'],['arrivalDate','Entrada'],['returnDeadline','Devolver antes de'],['price','Precio'],['stock','Existencia']],fields:[['publicationId','Publicación','publication',true],['number','Número / edición','text',true],['name','Nombre'],['barcode','Código de barras'],['arrivalDate','Fecha de entrada','date'],['returnDeadline','Fecha límite de devolución','date'],['price','Precio de venta','number',true],['stock','Existencia inicial','number',true]]},
  routes:{endpoint:'/routes',singular:'ruta',columns:[['name','Ruta'],['zone','Zona'],['deliveryDay','Día de reparto']],fields:[['name','Nombre','text',true],['zone','Zona'],['deliveryDay','Día de reparto','day']]},
  users:{endpoint:'/users',singular:'usuario',columns:[['username','Usuario'],['displayName','Nombre'],['role','Perfil'],['active','Estado']],fields:[['username','Usuario','text',true],['displayName','Nombre','text',true],['role','Perfil','role',true],['password','Contraseña','password',true]]}
};
async function renderCatalog(view){
  await loadBase();const meta=catalogMeta[view];const items=await api(meta.endpoint);state.data[view==='inventory'?'editions':view]=items;
  $('#content').innerHTML=`<div class="hero"><div><span class="eyebrow">CATÁLOGO</span><h1>${titles[view]}</h1><p>Consulta y registra la información de operación.</p></div><button id="add-record" class="primary">+ Nuevo ${meta.singular}</button></div><div class="panel"><div class="toolbar"><input id="search" placeholder="Buscar en ${titles[view].toLowerCase()}…"><span class="badge">${items.length} registros</span></div><div id="catalog-table">${catalogTable(meta,items)}</div></div>`;
  $('#search').oninput=e=>$('#catalog-table').innerHTML=catalogTable(meta,items.filter(x=>JSON.stringify(x).toLowerCase().includes(e.target.value.toLowerCase())));
  $('#add-record').onclick=()=>openRecordModal(view,meta);
}
function displayCell(key,value){
  if(['balance','creditLimit','price'].includes(key))return money(value);
  if(['arrivalDate','returnDeadline'].includes(key))return date(value);
  if(key==='supplierId')return esc(supplierName(value)); if(key==='publicationId')return esc(pubName(value));
  if(key==='active')return value?'<span class="badge">Activo</span>':'Inactivo';
  if(key==='role')return value==='Admin'?'Administrador':'Operador';
  if(key==='stock')return `<b class="${value<=3?'low':''}">${value}</b>`;
  return esc(value||'—');
}
function catalogTable(meta,items){if(!items.length)return '<div class="empty">No hay registros para mostrar</div>';const visible=items.slice(0,250);return `${items.length>250?`<div class="danger-note">Mostrando los primeros 250 de ${items.length.toLocaleString('es-MX')} registros. Usa la búsqueda para localizar uno específico.</div>`:''}<div class="table-wrap"><table><thead><tr>${meta.columns.map(c=>`<th>${c[1]}</th>`).join('')}</tr></thead><tbody>${visible.map(x=>`<tr>${meta.columns.map(c=>`<td>${displayCell(c[0],x[c[0]])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`}

async function openRecordModal(view,meta){
  await loadBase();
  const fields=meta.fields.map(([name,label,type='text',required=false])=>({name,label,type,required,options:type==='supplier'?state.data.suppliers.map(x=>[x.id,x.name]):type==='publication'?state.data.publications.map(x=>[x.id,x.title]):type==='role'?[['Operator','Operador'],['Admin','Administrador']]:type==='day'?['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'].map(x=>[x,x]):null}));
  openModal(`Nuevo ${meta.singular}`,fields,async values=>{await api(meta.endpoint,{method:'POST',body:JSON.stringify(values)});state.data={};toast(`${cap(meta.singular)} guardado correctamente`);$('#modal').close();navigate(view)});
}
function openModal(title,fields,onSubmit){
  $('#modal-title').textContent=title;$('#modal-error').textContent='';
  $('#modal-body').innerHTML=fields.map(f=>fieldHtml(f)).join('');
  const form=$('#modal-form');form.onsubmit=async e=>{e.preventDefault();const values={};fields.forEach(f=>{const el=form.elements[f.name];values[f.name]=f.type==='checkbox'?el.checked:['number','supplier','publication'].includes(f.type)?Number(el.value||0):el.value});try{await onSubmit(values)}catch(err){$('#modal-error').textContent=err.message}};
  $('#modal').showModal();
}
function fieldHtml(f){
  if(f.type==='checkbox')return `<label class="checkbox full"><input name="${f.name}" type="checkbox"> ${f.label}</label>`;
  if(f.options)return `<label>${f.label}<select name="${f.name}" ${f.required?'required':''}><option value="">Selecciona…</option>${f.options.map(o=>`<option value="${esc(o[0])}">${esc(o[1])}</option>`).join('')}</select></label>`;
  return `<label class="${['address'].includes(f.name)?'full':''}">${f.label}<input name="${f.name}" type="${f.type}" ${f.type==='number'?'step="0.01" min="0"':''} ${f.required?'required':''}></label>`;
}
const cap=s=>s.charAt(0).toUpperCase()+s.slice(1);

async function renderTransaction(view){
  await loadBase(true);state.transactionLines=[];const kind={sales:'Venta',purchases:'Compra',returns:'Devolución'}[view];const endpoint={sales:'sales',purchases:'purchases',returns:'returns'}[view];
  const party=view==='purchases'?`<label>Proveedor<select id="party"><option value="">Selecciona…</option>${state.data.suppliers.filter(x=>x.active).map(x=>`<option value="${x.id}">${esc(x.name)}</option>`).join('')}</select></label>`:`<label>Cliente<select id="party"><option value="">Selecciona…</option>${state.data.customers.filter(x=>x.active).map(x=>`<option value="${x.id}">${esc(x.name)}</option>`).join('')}</select></label>`;
  $('#content').innerHTML=`<div class="hero"><div><span class="eyebrow">OPERACIÓN</span><h1>${kind}</h1><p>Captura las partidas y confirma el movimiento.</p></div></div><div class="transaction-layout"><div class="transaction-panel">${view==='returns'?'<div class="danger-note">La devolución reincorpora ejemplares al inventario y disminuye el saldo del cliente.</div>':''}<div class="transaction-fields">${party}<label>Forma de pago<select id="payment-type"><option value="Cash">Contado</option><option value="Credit">Crédito</option><option value="Transfer">Transferencia</option></select></label></div><div class="line-add"><label>Edición<select id="line-edition"><option value="">Selecciona una edición…</option>${state.data.editions.filter(x=>x.active).map(x=>`<option value="${x.id}">${esc(editionName(x.id))} · ${x.stock} disp.</option>`).join('')}</select></label><label>Cantidad<input id="line-qty" type="number" min="1" value="1"></label><button id="add-line" class="secondary">Agregar</button></div><div id="lines"></div></div><aside class="transaction-panel"><h3>Resumen</h3><div id="summary"></div><label style="display:grid;gap:.4rem;font-size:.75rem;font-weight:700;margin:1rem 0">Notas<textarea id="notes" rows="3" style="border:1px solid var(--line);border-radius:10px;padding:.7rem"></textarea></label><button id="save-movement" class="primary wide">Confirmar ${kind.toLowerCase()} <span>→</span></button></aside></div>`;
  $('#add-line').onclick=()=>{const id=Number($('#line-edition').value),qty=Number($('#line-qty').value);if(!id||qty<=0)return toast('Selecciona una edición y cantidad');const existing=state.transactionLines.find(x=>x.editionId===id);if(existing)existing.quantity+=qty;else state.transactionLines.push({editionId:id,quantity:qty,discountPercent:0});renderLines()};
  $('#save-movement').onclick=async()=>{const partyId=Number($('#party').value);if(!partyId)return toast(`Selecciona un ${view==='purchases'?'proveedor':'cliente'}`);if(!state.transactionLines.length)return toast('Agrega al menos una partida');try{const body={customerId:view==='purchases'?null:partyId,supplierId:view==='purchases'?partyId:null,paymentType:$('#payment-type').value,notes:$('#notes').value,lines:state.transactionLines};const result=await api('/movements/'+endpoint,{method:'POST',body:JSON.stringify(body)});toast(`${kind} ${result.folio} registrada`);state.data={};navigate('dashboard')}catch(err){toast(err.message)}};
  renderLines();
}
function renderLines(){
  const lines=$('#lines'),summary=$('#summary');if(!lines)return;
  if(!state.transactionLines.length)lines.innerHTML='<div class="empty">Agrega publicaciones a este movimiento</div>';else lines.innerHTML=`<div class="table-wrap"><table><thead><tr><th>Publicación</th><th>Cant.</th><th>Precio</th><th>Importe</th><th></th></tr></thead><tbody>${state.transactionLines.map((x,i)=>{const e=state.data.editions.find(y=>y.id===x.editionId);return `<tr><td>${esc(editionName(x.editionId))}</td><td>${x.quantity}</td><td>${money(e.price)}</td><td><b>${money(e.price*x.quantity)}</b></td><td><button class="icon-button remove-line" data-index="${i}">×</button></td></tr>`}).join('')}</tbody></table></div>`;
  $$('.remove-line').forEach(x=>x.onclick=()=>{state.transactionLines.splice(Number(x.dataset.index),1);renderLines()});const total=state.transactionLines.reduce((sum,x)=>sum+state.data.editions.find(e=>e.id===x.editionId).price*x.quantity,0);summary.innerHTML=`<div class="summary-line"><span>Partidas</span><b>${state.transactionLines.length}</b></div><div class="summary-line"><span>Ejemplares</span><b>${state.transactionLines.reduce((s,x)=>s+x.quantity,0)}</b></div><div class="summary-line total"><span>Total</span><b>${money(total)}</b></div>`;
}

async function renderPayments(){
  await loadBase(true);const payments=await api('/payments');
  $('#content').innerHTML=`<div class="hero"><div><span class="eyebrow">CUENTAS POR COBRAR</span><h1>Abonos</h1><p>Registra pagos y consulta los últimos cobros.</p></div><button id="new-payment" class="primary">+ Registrar abono</button></div><div class="cards">${metric('Saldo total',money(state.data.customers.reduce((s,x)=>s+x.balance,0)),'$','Cartera vigente')}${metric('Clientes con saldo',state.data.customers.filter(x=>x.balance>0).length,'◉','Requieren seguimiento')}</div><div class="panel" style="margin-top:1rem"><div class="panel-head"><h3>Últimos abonos</h3></div>${payments.length?`<div class="table-wrap"><table><thead><tr><th>Fecha</th><th>Cliente</th><th>Método</th><th>Referencia</th><th>Importe</th></tr></thead><tbody>${payments.map(x=>`<tr><td>${date(x.createdAt)}</td><td>${esc(customerName(x.customerId))}</td><td>${esc(x.method)}</td><td>${esc(x.reference||'—')}</td><td><b>${money(x.amount)}</b></td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">Aún no hay abonos</div>'}</div>`;
  $('#new-payment').onclick=()=>openModal('Registrar abono',[{name:'customerId',label:'Cliente',type:'supplier',required:true,options:state.data.customers.filter(x=>x.balance>0).map(x=>[x.id,`${x.name} · saldo ${money(x.balance)}`])},{name:'amount',label:'Importe',type:'number',required:true},{name:'method',label:'Método',options:[['Cash','Efectivo'],['Transfer','Transferencia'],['Card','Tarjeta']]},{name:'reference',label:'Referencia'}],async values=>{await api('/payments',{method:'POST',body:JSON.stringify(values)});$('#modal').close();state.data={};toast('Abono registrado');navigate('payments')});
}
async function renderReports(){await loadBase(true);const moves=await api('/movements');$('#content').innerHTML=`<div class="hero"><div><span class="eyebrow">HISTORIAL</span><h1>Movimientos</h1><p>Ventas, compras y devoluciones en una sola consulta.</p></div></div><div class="panel"><div class="toolbar"><input id="search" placeholder="Buscar por folio…"><select id="move-filter" class="secondary"><option value="">Todos</option><option value="Sale">Ventas</option><option value="Purchase">Compras</option><option value="Return">Devoluciones</option></select></div><div id="moves">${movementTable(moves)}</div></div>`;const refresh=()=>{const q=$('#search').value.toLowerCase(),type=$('#move-filter').value;$('#moves').innerHTML=movementTable(moves.filter(x=>(!type||x.type===type)&&JSON.stringify(x).toLowerCase().includes(q)))};$('#search').oninput=refresh;$('#move-filter').onchange=refresh}

if(state.token) api('/auth/me').then(u=>{state.user=u;start()}).catch(logout);
