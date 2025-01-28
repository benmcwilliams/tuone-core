```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Acme-Solar" or company = "Acme Solar")
sort location, dt_announce desc
```
