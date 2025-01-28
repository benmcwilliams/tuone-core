```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Plataforma-Solar-de-Almería" or company = "Plataforma Solar de Almería")
sort location, dt_announce desc
```
