```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Empresa-de-Eletrciidade-dos-Açores" or company = "Empresa de Eletrciidade dos Açores")
sort location, dt_announce desc
```
