```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Institut-des-Matériaux-Jean-Rouxel" or company = "Institut des Matériaux Jean Rouxel")
sort location, dt_announce desc
```
