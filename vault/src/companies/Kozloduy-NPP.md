```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Kozloduy-NPP" or company = "Kozloduy NPP")
sort location, dt_announce desc
```
