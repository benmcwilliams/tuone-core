```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Empresa de Desenvolvimento e Infraestruturas do Alqueva"
sort location, dt_announce desc
```
