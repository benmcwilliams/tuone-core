```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Allianz-Capital-Partners" or company = "Allianz Capital Partners")
sort location, dt_announce desc
```
