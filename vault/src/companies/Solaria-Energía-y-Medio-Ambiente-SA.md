```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Solaria Energía y Medio Ambiente SA"
sort location, dt_announce desc
```
