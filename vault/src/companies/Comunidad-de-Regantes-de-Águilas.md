```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Comunidad de Regantes de Águilas"
sort location, dt_announce desc
```
