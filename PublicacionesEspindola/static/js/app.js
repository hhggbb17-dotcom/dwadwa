const menuData = [
  ['🗂','1.Catalogos',[
    ['1.Proveedores','catalog','suppliers'],
    ['2.Clientes',null,null,[['1.Prioridades','report'],['2.Grupos de Clientes','report'],['3.Altas','form','customers'],['4.Consultas','catalog','customers'],['5.Modificaciones','catalog','customers'],['7.Modificaciones de Sucursal','report'],['8.Reportes','report'],['9.Rutas','report']]],
    ['3.Revistas','catalog','publications'],['4.Empleados','report'],['5.Cuentas','report']]],
  ['📄','2.Compras',[
    ['1.Facturas','operation','COMPRA'],
    ['2.Cuentas por Pagar',null,null,[['1.Altas','operation','CUENTA POR PAGAR'],['2.Consultas','operations'],['3.Reporte de Liquidacion','report'],['4.Estado de Cuenta','report']]],
    ['3.Devoluciones',null,null,[['1.Altas','operation','DEVOLUCION A PROVEEDOR'],['2.Reportes de Predevolucion','report'],['3.Consultas','operations']]],
    ['4.Reporte Estadistico de Compras','report']]],
  ['📰','3.Ventas',[
    ['1.Paquetes',null,null,[['1.Altas','operation','PAQUETE'],['2.Consultas','operations'],['3.Paquete Maestro','report'],['4.Reporte Distribucion de Locales Cerrados','report']]],
    ['2.Pedidos',null,null,[['1.Consultas','operations']]],
    ['3.Facturas',null,null,[['1.Altas','operation','VENTA'],['2.Consultas','operations'],['3.Para Contabilidad','report'],['4.Relacion Tiket','report'],['5.Alta x Grupos','report'],['6.Reporte de Rutas','report'],['7.Reporte de Venta x Revistas','report'],['8.Reporte Mensual SAT','report']]],
    ['4.Devoluciones',null,null,[['1.Normal','operation','DEVOLUCION DE CLIENTE'],['2.Cancelacion','operation','CANCELACION'],['3.Extemporanea','operation','DEVOLUCION EXTEMPORANEA'],['4.Consultas','operations'],['5.Para Contabilidad','report'],['6.Relacion Tikets','report'],['7.Reporte de Pre-Devolucion','report'],['8.Rep. de Devoluciones x Revista','report']]],
    ['5.Cuentas por Cobrar',null,null,[['1.Altas','operation','CUENTA POR COBRAR'],['2.Consultas','operations'],['3.Estado de Cuenta','report'],['4.Estado de Cuenta x Grupo','report']]],
    ['6.Corte de Caja',null,null,[['1.Del Dia General','report'],['2.Flujo de Efectivo','report'],['3.Corte detallado','report'],['4.Consulta de Vales','report'],['5.Movimientos de Clientes','report']]],
    ['7.Reporte de Distribucion','report'],['8.Conciliacion','report'],['9.Reporte Estadistico de Ventas','report']]],
  ['A','4.Inventario',[
    ['1.Ediciones',null,null,[['1.Consultas','catalog','editions'],['2.Modificaciones','catalog','editions'],['3.Reporte de Existencias x Revista','report'],['4.Reporte de Inventario','report']]],
    ['2.Traspasos',null,null,[['1.Alta de Traspasos','operation','TRASPASO'],['2.Consulta','operations']]],
    ['3.Tipo de Movimientos',null,null,[['1.Altas','report'],['2.Consultas','report'],['3.Modificaciones','report']]]]],
  ['🚫','5.Cancelaciones', [['1.Compras','operation','CANCELACION DE COMPRA'],['3.Devolucion x Bodega','operation','DEVOLUCION POR BODEGA'],['4.Devolucion x Devolucion','operation','CANCELACION DE DEVOLUCION']]],
  ['❔','8.Ayuda', [['Acerca de SADYV','about']]],
  ['🔧','9.Salir', [['Salir del sistema','exit']]]
];

const toolbar = [
  ['💰','Ventas',()=>openOperation('VENTA')],['▤','Consultas',()=>openCatalog('operations','Consulta de Ventas')],
  ['👥','Clientes',()=>openCatalog('customers','MODULO DE CLIENTES')],['▰','Edo.Cta.',()=>openReport('Estado de Cuenta')],
  ['▦','Flujo Efec.',()=>openReport('Flujo de Efectivo')],['◀','Devolucion',()=>openOperation('DEVOLUCION DE CLIENTE')],
  ['▣','Consultas',()=>openCatalog('editions','Consulta de Ediciones')]
];

const columns = {
  customers: [['code','Clave'],['name','Nombre'],['rfc','R.F.C.'],['phone','Teléfono'],['city','Ciudad'],['balance','Saldo']],
  suppliers: [['code','Clave'],['name','Nombre'],['rfc','Reg. Fed. Caus.'],['phone','Teléfono'],['balance','Saldo']],
  publications: [['code','Clave revista'],['title','Título'],['barcode','Código de barras'],['tax','I.V.A.']],
  editions: [['publication_code','Clave revista'],['title','Nombre Revista'],['number','No. Edición'],['name','Edición'],['price','Precio'],['stock','Existencia'],['arrival_date','Fecha Entrada']],
  operations: [['kind','Movimiento'],['folio','Folio'],['operation_date','Fecha'],['party_code','Clave'],['party_name','Nombre'],['total','Total']]
};

function buildMenus(){
  const nav=document.querySelector('#main-menu');
  menuData.forEach(([icon,label,items])=>{
    const root=document.createElement('div'); root.className='menu-root';
    root.innerHTML=`<button class="menu-label"><span class="ico">${icon}</span>${label}</button>`;
    root.appendChild(dropdown(items)); nav.appendChild(root);
    root.firstChild.onclick=e=>{e.stopPropagation();document.querySelectorAll('.menu-root').forEach(x=>x!==root&&x.classList.remove('open'));root.classList.toggle('open')};
  });
  document.onclick=()=>document.querySelectorAll('.menu-root').forEach(x=>x.classList.remove('open'));
}
function dropdown(items){
  const d=document.createElement('div');d.className='dropdown';
  items.forEach(([label,action,arg,children])=>{
    const holder=document.createElement(children?'div':'button');holder.className=children?'submenu-item':'menu-item';
    if(children){holder.innerHTML=`<button class="menu-item has-next">${label}</button>`;holder.appendChild(dropdown(children));}
    else{holder.textContent=label;holder.onclick=e=>{e.stopPropagation();run(action,arg,label);closeMenus()};}
    d.appendChild(holder);
  });return d;
}
function closeMenus(){document.querySelectorAll('.menu-root').forEach(x=>x.classList.remove('open'))}
function run(action,arg,label){
  if(action==='catalog')openCatalog(arg,label); else if(action==='form')openForm(arg);
  else if(action==='operation')openOperation(arg); else if(action==='operations')openCatalog('operations',label);
  else if(action==='report')openReport(label); else if(action==='about')openAbout();
  else if(action==='exit')window.close();
}
function buildToolbar(){const t=document.querySelector('#toolbar');toolbar.forEach(([i,l,fn])=>{const b=document.createElement('button');b.className='tool';b.innerHTML=`<span class="tool-icon">${i}</span>${l}`;b.onclick=fn;t.appendChild(b)})}
function win(title,compact=false){
  document.querySelectorAll('.mdi-window').forEach(x=>x.remove());
  const w=document.createElement('section');w.className='mdi-window'+(compact?' compact':'');
  w.innerHTML=`<div class="mdi-title"><span>▧</span>&nbsp;<b>${title}</b><div class="mdi-controls"><button>_</button><button>□</button><button class="close">×</button></div></div>`;
  w.querySelector('.close').onclick=()=>w.remove();document.querySelector('#windows').appendChild(w);return w;
}
async function openCatalog(entity,title){
  const w=win(title || entity.toUpperCase());
  w.insertAdjacentHTML('beforeend',`<div class="module-nav"><button>Altas</button><button>Consultas</button><button>Modificaciones</button><button class="nav-exit">Salir</button></div><div class="module-heading"><strong>CARLOS ESPINDOLA</strong><strong>CARLOS ESPINDOLA</strong><span>Catálogo de ${title||entity}</span></div><div class="searchbar"><label>Buscar&nbsp; <input class="query" autofocus></label><button class="win-button find">🔎 Buscar</button><button class="win-button add">➕ Alta</button></div><div class="table-wrap"><table class="data-table"><thead><tr>${columns[entity].map(x=>`<th>${x[1]}</th>`).join('')}</tr></thead><tbody></tbody></table></div><div class="status-mini">${today()} &nbsp;&nbsp; Consulta del catálogo</div>`);
  w.querySelector('.nav-exit').onclick=()=>w.remove(); w.querySelector('.add').onclick=()=>entity==='operations'?openOperation('MOVIMIENTO'):openForm(entity);
  const load=async()=>{const rows=await fetch(`/api/${entity}?q=${encodeURIComponent(w.querySelector('.query').value)}`).then(r=>r.json());w.querySelector('tbody').innerHTML=rows.map(row=>`<tr>${columns[entity].map(([key])=>`<td>${format(row[key],key)}</td>`).join('')}</tr>`).join('')};
  w.querySelector('.find').onclick=load;w.querySelector('.query').onkeydown=e=>e.key==='Enter'&&load();load();
}
function formFields(entity){
  if(entity==='customers')return [['code','Clave'],['rfc','R. F. C.'],['name','Nombre','wide'],['address','Dirección','wide'],['city','Ciudad'],['phone','Teléfono(s)'],['email','Email'],['discount','Descuento (%)'],['credit_limit','Límite Crédito'],['balance','Saldo Inicial']];
  if(entity==='suppliers')return [['code','Clave'],['rfc','Reg. Fed. Caus.'],['name','Nombre'],['address','Dirección'],['phone','Teléfono'],['email','Email'],['balance','Saldo']];
  return [['code','Clave revista'],['supplier_id','Clave Proveedor'],['title','Nombre Revista','wide'],['barcode','Código de Barras'],['tax','I.V.A. (%)']];
}
function openForm(entity){
  const names={customers:'MODULO DE CLIENTES',suppliers:'Modulo de Proveedores',publications:'Modulo de Revistas'};const w=win(names[entity]||'Catálogo',true);const fields=formFields(entity);
  w.insertAdjacentHTML('beforeend',`<div class="module-nav"><button>Altas</button><button>Consultas</button><button>Modificaciones</button><button class="nav-exit">Salir</button></div><div class="module-heading"><strong>CARLOS ESPINDOLA</strong><strong>CARLOS ESPINDOLA</strong><span>Alta de ${entity==='customers'?'cliente':entity==='suppliers'?'proveedor':'revista'}</span></div><div class="tabs"><button class="tab">Datos Generales</button><button class="tab">Condiciones</button></div><form class="form-area"><div class="form-grid">${fields.map(([key,label,wide])=>`<label>${label}</label><input name="${key}" class="${wide==='wide'?'span3':''}">`).join('')}</div></form><div class="button-row"><button class="win-button save">💾 Guardar</button><button class="win-button nav-exit">🚪 Salir</button></div><div class="status-mini">${today()} &nbsp;&nbsp; CLAVE DEL REGISTRO</div>`);
  w.querySelectorAll('.nav-exit').forEach(b=>b.onclick=()=>w.remove());
  w.querySelector('.save').onclick=async()=>{const data=Object.fromEntries(new FormData(w.querySelector('form')));const r=await fetch(`/api/${entity}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const out=await r.json();if(r.ok){toast('Registro guardado correctamente');w.remove();openCatalog(entity,names[entity])}else toast(out.error||'No fue posible guardar')};
}
function openOperation(kind){
  const title=kind.includes('COMPRA')?'Modulo de Compras':kind.includes('PROVEEDOR')?'Devolucion a Proveedores(Almacen Devoluciones)':kind==='VENTA'?'Modulo de Ventas':kind;const w=win(title);
  const folio=String(Date.now()).slice(-6);w.insertAdjacentHTML('beforeend',`<div class="operation-head"><label>Folio Interno</label><input name="folio" value="${folio}" readonly><label>Fecha</label><input name="operation_date" value="${today()}"><label>Clave ${kind.includes('COMPRA')?'Proveedor':'Cliente'}</label><input name="party_code"><label>Nombre</label><input name="party_name"></div><div class="ledger"><table class="data-table"><thead><tr><th>Clave revista</th><th>Nombre Revista</th><th>No.Edición</th><th>Precio</th><th>Cantidad</th><th>Descuento</th><th>Importe</th><th>Monto Gravado</th></tr></thead><tbody><tr class="selected"><td>&nbsp;</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tbody></table></div><div class="totals"><div>Total de Partidas:&nbsp; 0<br><br>Total de Revistas:&nbsp; 0</div><div class="total-box"><label>Exento</label><input value="$       0.00" readonly><label>Gravado</label><input value="$       0.00" readonly><label>I.V.A.</label><input value="$       0.00" readonly><label>Total</label><input name="total" value="0.00"></div></div><div class="button-row"><button class="win-button save">💾 Guardar(F2)</button><button class="win-button close-op">🚪 Salir</button><button class="win-button">📖 Dar de Alta Otra</button></div><div class="status-mini">${today()} &nbsp;&nbsp;&nbsp;&nbsp; Folio de la operación</div>`);
  w.querySelector('.close-op').onclick=()=>w.remove();w.querySelector('.save').onclick=async()=>{const q=n=>w.querySelector(`[name=${n}]`).value;const data={kind,folio:q('folio'),operation_date:isoDate(q('operation_date')),party_code:q('party_code'),party_name:q('party_name'),total:q('total'),notes:''};const r=await fetch('/api/operations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});if(r.ok){toast('Movimiento guardado correctamente');w.remove()}else toast('No fue posible guardar el movimiento')};
}
function openReport(title){const w=win(title,true);w.insertAdjacentHTML('beforeend',`<div class="module-heading"><strong>CARLOS ESPINDOLA</strong><strong>${title}</strong></div><div class="form-area"><fieldset><legend>Parámetros del reporte</legend><div class="form-grid"><label>Fecha Inicial</label><input value="${today()}"><label>Fecha Final</label><input value="${today()}"><label>Clave Inicial</label><input><label>Clave Final</label><input></div></fieldset><p>Seleccione los parámetros para consultar la información.</p></div><div class="button-row"><button class="win-button" onclick="window.print()">🖨 Imprimir</button><button class="win-button close-report">🚪 Salir</button></div><div class="status-mini">${today()} &nbsp;&nbsp; ${title}</div>`);w.querySelector('.close-report').onclick=()=>w.remove()}
function openAbout(){const w=win('Acerca de SADYV',true);w.insertAdjacentHTML('beforeend',`<div class="form-area" style="text-align:center;padding-top:70px"><h2>SADYV</h2><p>SISTEMA DE ADMINISTRACION DISTRIBUCION Y VENTA DE REVISTAS</p><p>CARLOS ESPINDOLA</p><p>Versión Web local para Windows 11</p></div><div class="button-row"><button class="win-button close-about">Aceptar</button></div>`);w.querySelector('.close-about').onclick=()=>w.remove()}
function toast(msg){const t=document.createElement('div');t.className='toast';t.textContent=msg;document.querySelector('#desktop').appendChild(t);setTimeout(()=>t.remove(),2600)}
function format(v,key){if(v==null)return '';if(['balance','price','total'].includes(key))return Number(v).toLocaleString('es-MX',{style:'currency',currency:'MXN'});return String(v).replaceAll('&','&amp;').replaceAll('<','&lt;')}
function today(){return document.body.dataset.today}function isoDate(d){const [a,m,y]=d.split('/');return `${y}-${m}-${a}`}
buildMenus();buildToolbar();setInterval(()=>document.querySelector('#clock').textContent=new Date().toLocaleTimeString('es-MX'),1000);
