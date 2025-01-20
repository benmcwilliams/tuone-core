```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Instituto Tecnologico de Canarias"
sort location, dt_announce desc
```
