--Metalzoa (historical implementation, Retro Formats)
--Original script for edopro-retro-formats (MIT). Written from the period card text
--and the engine's Lua API; it is not a copy or an adaptation of any Project Ignis
--CardScripts file, whose licence (AGPL-3.0-or-later) this repository does not carry.
--
--Period text: "This monster can only be Special Summoned from your Deck to your side
--of the field by offering "Zoa" equipped with "Metalmorph" as a Tribute."
--
--Implemented: it can never be Normal Summoned or Set, and can be Special Summoned
--only by the procedure below, from the Deck, Tributing a face-up "Zoa" you control
--that is equipped with "Metalmorph". Unlike the modern card, nothing else can ever
--Special Summon it, so it cannot be revived from the Graveyard or banished zone.
--See data/custom-cards/c600000001.json for what this script does not reproduce.
local s,id=GetID()
local CARD_ZOA=24311372
local CARD_METALMORPH=68540058
function s.initial_effect(c)
	--cannot be Normal Summoned or Set
	local e0=Effect.CreateEffect(c)
	e0:SetType(EFFECT_TYPE_SINGLE)
	e0:SetProperty(EFFECT_FLAG_CANNOT_DISABLE+EFFECT_FLAG_UNCOPYABLE)
	e0:SetCode(EFFECT_CANNOT_SUMMON)
	c:RegisterEffect(e0)
	local e1=e0:Clone()
	e1:SetCode(EFFECT_CANNOT_MSET)
	c:RegisterEffect(e1)
	--can only be Special Summoned by its own procedure
	local e2=Effect.CreateEffect(c)
	e2:SetType(EFFECT_TYPE_SINGLE)
	e2:SetProperty(EFFECT_FLAG_CANNOT_DISABLE+EFFECT_FLAG_UNCOPYABLE)
	e2:SetCode(EFFECT_SPSUMMON_CONDITION)
	e2:SetValue(aux.FALSE)
	c:RegisterEffect(e2)
	--Special Summon from the Deck by Tributing "Zoa" equipped with "Metalmorph"
	local e3=Effect.CreateEffect(c)
	e3:SetType(EFFECT_TYPE_FIELD)
	e3:SetProperty(EFFECT_FLAG_UNCOPYABLE)
	e3:SetCode(EFFECT_SPSUMMON_PROC)
	e3:SetRange(LOCATION_DECK)
	e3:SetCondition(s.spcon)
	e3:SetOperation(s.spop)
	c:RegisterEffect(e3)
end
function s.zoafilter(c,tp)
	return c:IsFaceup() and c:IsCode(CARD_ZOA)
		and c:GetEquipGroup():IsExists(s.equipfilter,1,nil)
		and Duel.GetMZoneCount(tp,c)>0
end
function s.equipfilter(c)
	return c:IsCode(CARD_METALMORPH)
end
function s.spcon(e,c)
	if c==nil then return true end
	local tp=c:GetControler()
	return Duel.IsExistingMatchingCard(s.zoafilter,tp,LOCATION_MZONE,0,1,nil,tp)
end
function s.spop(e,tp,eg,ep,ev,re,r,rp,c)
	Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_RELEASE)
	local g=Duel.SelectMatchingCard(tp,s.zoafilter,tp,LOCATION_MZONE,0,1,1,nil,tp)
	if #g>0 then
		Duel.Release(g,REASON_COST)
	end
end
