```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Empresa-Municipal-de-Transportes-de-Madrid" or company = "Empresa Municipal de Transportes de Madrid")
sort location, dt_announce desc
```
