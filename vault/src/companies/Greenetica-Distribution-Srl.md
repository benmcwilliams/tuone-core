```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Greenetica-Distribution-Srl" or company = "Greenetica Distribution Srl")
sort location, dt_announce desc
```
