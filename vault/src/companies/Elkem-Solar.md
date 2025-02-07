```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Elkem-Solar" or company = "Elkem Solar")
sort location, dt_announce desc
```
