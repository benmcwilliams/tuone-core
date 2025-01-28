```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Helmholtz-Centre-for-Environmental-Research-Leipzig" or company = "Helmholtz Centre for Environmental Research Leipzig")
sort location, dt_announce desc
```
